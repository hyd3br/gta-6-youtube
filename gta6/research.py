"""Bounded primary-source collection with evidence and conservative fact extraction."""
from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler

PRIMARY_HOSTS = frozenset({'www.rockstargames.com', 'rockstargames.com',
                           'www.take2games.com', 'ir.take2games.com'})
MAX_BYTES = 4_000_000


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Fonte deve usar HTTPS sem credenciais ou porta alternativa.')
    if p.hostname not in PRIMARY_HOSTS:
        raise ValueError('Coleta automática limitada aos domínios primários configurados.')
    # Reject path escaping and keep only publisher page identities, not trackers.
    return urlunsplit(('https', p.hostname, p.path.rstrip('/') or '/', '', ''))


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, canonical(newurl))


def fetch(url):
    url = canonical(url)
    req = Request(url, headers={'User-Agent': 'GTA6EditorialResearch/0.1 (local human-reviewed research)',
                                'Accept': 'text/html, application/rss+xml, application/xml'})
    with build_opener(SafeRedirect).open(req, timeout=25) as response:
        canonical(response.url)
        if not any(t in response.headers.get('Content-Type', '') for t in ('html', 'xml', 'text/plain')):
            raise ValueError('A fonte não devolveu HTML/XML legível.')
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Página excede o limite de coleta.')
        return raw.decode('utf-8', errors='replace')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.metadata, self.jsonld = [], [], {}, []
        self.hidden = 0
        self.in_title = False
        self.title = ''
        self.ld = False
        self.script = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style', 'nav', 'footer', 'noscript'):
            self.hidden += 1
        if tag == 'script':
            self.ld = a.get('type') == 'application/ld+json'
            self.script = ''
        if tag == 'title': self.in_title = True
        if tag == 'meta':
            self.metadata[a.get('property', a.get('name', ''))] = a.get('content', '')
        if tag == 'a' and a.get('href'): self.links.append(a['href'])

    def handle_endtag(self, tag):
        if tag == 'script' and self.ld:
            try: self.jsonld.append(json.loads(self.script))
            except json.JSONDecodeError: pass
            self.ld = False
        if tag in ('script', 'style', 'nav', 'footer', 'noscript'):
            self.hidden = max(0, self.hidden - 1)
        if tag == 'title': self.in_title = False

    def handle_data(self, data):
        if self.ld: self.script += data
        if self.in_title: self.title += data
        if not self.hidden and data.strip(): self.parts.append(data.strip())


def parse_page(raw, url):
    p = Page()
    p.feed(raw)
    published = p.metadata.get('article:published_time')
    extra = []

    def visit(node):
        nonlocal published
        if isinstance(node, list):
            for n in node: visit(n)
        if isinstance(node, dict):
            if node.get('@type') in ('NewsArticle', 'Article', 'BlogPosting', 'VideoGame'):
                if node.get('articleBody'): extra.append(str(node['articleBody']))
                if node.get('description'): extra.append(str(node['description']))
                published = published or node.get('datePublished')
            if '@graph' in node: visit(node['@graph'])
    for n in p.jsonld: visit(n)
    # Official social/SEO descriptions often contain the only server-rendered
    # editorial copy on a JS-heavy site. They are publisher-authored evidence too.
    for key in ('description','og:description','twitter:description'):
        if p.metadata.get(key): extra.append(p.metadata[key])
    text = re.sub(r'\s+', ' ', html.unescape(' '.join(p.parts + extra))).strip()
    title = p.metadata.get('og:title') or p.title.strip() or url
    if len(text) < 100 or any(x in title.lower() for x in ('access denied', 'just a moment', 'captcha')):
        raise ValueError('Página sem conteúdo editorial legível; pode exigir JavaScript ou bloquear coleta.')
    return {'title': title, 'text': text, 'published_at': published,
            'links': p.links, 'fetched_at': now(), 'url': canonical(url),
            'sha256': digest(raw), 'source_type': 'primary'}


# Deliberately small, auditable vocabulary. No release dates, FPS or gameplay claims.
# Each fact requires an explicit contiguous evidence span, never a generated inference.
RULES = [
    ('setting', r'(?:state of Leonida|estado de Leonida)',
     'A ambientação oficial de GTA seis inclui o estado de Leonida.',
     'LEONIDA É O CENÁRIO',
     'Ambientação não é uma medida de escala. O nome de um estado fictício não permite calcular a área jogável, contar cidades ou prometer interiores acessíveis. Para isso, precisamos de informações específicas sobre o mapa.'),
    ('vice_city', r'(?:home to|including|incluindo|lar de)[^.!?]{0,90}Vice City',
     'Vice City faz parte da ambientação apresentada para GTA seis.',
     'VICE CITY NO CONTEXTO',
     'Reconhecer uma cidade e conhecer suas regras são coisas diferentes. Um cenário pode estabelecer identidade visual sem demonstrar atividades disponíveis. Nossa análise separa o lugar apresentado das mecânicas que ainda precisam de evidência.'),
    ('protagonists', r'Jason and Lucia|Jason e Lucia',
     'O material oficial apresenta Jason e Lucia na história de GTA seis.',
     'JASON E LUCIA',
     'A apresentação de dois personagens não revela, sozinha, como o controle alterna entre eles. Relação narrativa, estrutura das missões e decisões do jogador exigem demonstrações próprias. É possível discutir possibilidades sem anunciar uma mecânica inexistente.'),
    ('ps5', r'PlayStation\s*(?:®\s*)?5|PS5',
     'PlayStation cinco aparece entre as plataformas na página oficial consultada.',
     'PLATAFORMAS E LIMITES',
     'Listar uma plataforma não comprova taxa de quadros, resolução interna ou desempenho estável. Esses detalhes precisam de medições ou comunicação técnica. Nosso roteiro não transforma uma marca de console numa promessa de sessenta quadros por segundo.'),
    ('xbox', r'Xbox Series X\s*(?:\||/|and|e|&amp;|&)\s*S|Xbox Series X and Series S',
     'Xbox Series X e S aparecem entre as plataformas no material oficial consultado.',
     'O QUE A LISTA NÃO PROVA',
     'Um anúncio de plataformas registra uma intenção de lançamento no momento em que foi publicado. Ele não demonstra paridade gráfica entre aparelhos. Também não autoriza concluir que uma versão para outro sistema foi anunciada ou cancelada.'),
]


def extract_facts(page):
    if page.get('source_type') != 'primary' or canonical(page['url']) != page['url']:
        raise ValueError('Proveniência primária inválida.')
    # Facts must be in a GTA VI-specific page/body, not an unrelated corporate index.
    text = page['text']
    if not re.search(r'Grand Theft Auto VI|GTA\s*(?:VI|6)|/VI(?:/|$)', text + ' ' + page['url'], re.I):
        return []
    facts = []
    for key, pattern, statement, headline, analysis in RULES:
        match = re.search(pattern, text, re.I)
        if not match: continue
        nearby=text[max(0,match.start()-400):min(len(text),match.end()+400)]
        if '/VI' not in urlsplit(page['url']).path and not re.search(r'Grand Theft Auto VI|GTA\s*(?:VI|6)',nearby,re.I):
            continue
        excerpt = text[max(0, match.start()-100):min(len(text), match.end()+130)]
        # Do not convert explicit questions, negations or speculation into confirmation.
        if re.search(r'rumou?r|unconfirmed|not confirmed|não confirmado|might|could|cancel|não inclui|not include|not available|will not|não estará', excerpt, re.I):
            continue
        facts.append({'id': digest('gta6:' + key)[:20], 'key': key, 'statement': statement,
                      'headline': headline, 'analysis': analysis, 'classification': 'confirmed',
                      'evidence': match.group(), 'context': excerpt,
                      'source_url': page['url'], 'source_title':page['title'], 'source_sha256': page['sha256'],
                      'checked_at': page['fetched_at'], 'published_at': page['published_at']})
    return facts


class Store:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.folder/'editorial.sqlite3')
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS sources (url TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS facts (id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY, topic_key TEXT NOT NULL, format TEXT NOT NULL,
            status TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(topic_key, format));
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY, episode_id TEXT NOT NULL, decision TEXT NOT NULL,
            note TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')

    def save_page(self, page, raw):
        snapshots = self.folder/'snapshots'
        snapshots.mkdir(exist_ok=True)
        (snapshots/(page['sha256']+'.html')).write_text(raw, encoding='utf-8')
        self.db.execute('INSERT OR REPLACE INTO sources VALUES (?,?)', (page['url'],json.dumps(page,ensure_ascii=False)))
        for fact in extract_facts(page):
            self.db.execute('INSERT OR REPLACE INTO facts VALUES (?,?)', (fact['id'],json.dumps(fact,ensure_ascii=False)))
        self.db.commit()

    def facts(self, max_age_hours=48):
        result = []
        for row in self.db.execute('SELECT body FROM facts ORDER BY id'):
            fact = json.loads(row['body'])
            age = (datetime.now(timezone.utc)-datetime.fromisoformat(fact['checked_at'])).total_seconds()/3600
            page_row = self.db.execute('SELECT body FROM sources WHERE url=?',(fact['source_url'],)).fetchone()
            # Source changed? A removed claim must not survive an updated page.
            if page_row and json.loads(page_row['body'])['sha256']==fact['source_sha256'] and 0<=age<=max_age_hours:
                result.append(fact)
        return result


def collect(store, seeds, max_pages=12, fetcher=fetch):
    pending = list(dict.fromkeys(canonical(s) for s in seeds))
    if not 1<=max_pages<=30: raise ValueError('max_pages deve ficar entre 1 e 30.')
    seen, errors, pages = set(), [], []
    while pending and len(seen)<max_pages:
        url = pending.pop(0)
        if url in seen: continue
        seen.add(url)
        try:
            raw = fetcher(url)
            page = parse_page(raw,url)
            store.save_page(page,raw)
            pages.append({'url':url,'sha256':page['sha256'],'published_at':page['published_at']})
            for href in page['links']:
                if not any(k in href for k in ('/newswire/article/', '/news-releases/', '/press-release', '/news/')):
                    continue
                try: link=canonical(urljoin(url,href))
                except ValueError: continue
                if link not in seen and link not in pending: pending.append(link)
        except Exception as e:
            # Persist a concise, non-secret diagnosis. Do not dump HTTP headers/response bodies.
            errors.append({'url':url,'error_type':type(e).__name__,'message':str(e)[:250]})
    report={'collected_at':now(),'pages':pages,'errors':errors,'fresh_facts':len(store.facts()),
            'complete':not errors,'pending_pages':len(pending)}
    (store.folder/'last_research.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
