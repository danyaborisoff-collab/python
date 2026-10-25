"""Встроенная проверка доставки: ссылки/якоря/локальные ресурсы/контрольная строка."""
import json,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

class Parser(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=set();self.canonical=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href')
        if 'id' in a:self.ids.add(a['id'])
        for key in ('href','src'):
            if key in a:self.refs.append((tag,key,a[key]))

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'site').resolve()
    pages={p:Parser() for p in root.rglob('*.html')}
    for p,obj in pages.items():obj.feed(p.read_text(encoding='utf-8'))
    errors=[]
    base=urlsplit(pages[root/'index.html'].canonical or '').path
    if base.endswith('index.html'):base=base[:-10]
    if not base.endswith('/'):base+='/'
    for p,obj in pages.items():
        for tag,key,ref in obj.refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc:
                # Гиперссылки на источники допустимы, внешние runtime-ресурсы — нет.
                if tag in ('script','img','iframe','link') and key in ('href','src') and u.scheme in ('http','https'):
                    # canonical URL, sitemap и RSS не являются ресурсами отображения.
                    if tag!='link' or ref.endswith('.css'):
                        errors.append(f'{p.relative_to(root)}: external runtime resource {ref}')
                continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            if u.path.startswith('/'):
                # 404 может обслуживаться на любой глубине; Material намеренно
                # использует префикс site_url, а не относительные пути.
                if p==root/'404.html' and u.path.startswith(base):
                    target=(root/unquote(u.path[len(base):])).resolve()
                else:
                    errors.append(f'{p.relative_to(root)}: root-relative URL {ref}');continue
            if not target.is_relative_to(root):errors.append(f'path escapes site: {ref}');continue
            if target.is_dir():target=target/'index.html'
            if not target.exists():errors.append(f'{p.relative_to(root)}: missing {ref}')
            elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
                errors.append(f'{p.relative_to(root)}: missing anchor {ref}')
    assert 'RESEARCH-SITE-OK' in (root/'index.html').read_text(encoding='utf-8')
    assert 'RESEARCH-SITE-OK' in (root/'generated/results.html').read_text(encoding='utf-8')
    search=json.loads((root/'search/search_index.json').read_text(encoding='utf-8'))
    assert search['docs'],'empty search index'
    if errors:raise SystemExit('\n'.join(errors))
    print(f'PASS site: {len(pages)} HTML pages, internal links/anchors, local resources and search index')
if __name__=='__main__':main()
