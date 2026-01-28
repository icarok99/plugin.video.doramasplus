# -*- coding: utf-8 -*-
import sys
import os

try:
    from urllib.parse import urlparse, parse_qs, quote, unquote, quote_plus, unquote_plus, urlencode
except ImportError:    
    from urlparse import urlparse, parse_qs
    from urllib import quote, unquote, quote_plus, unquote_plus, urlencode

import requests
from bs4 import BeautifulSoup
import re
import base64
import json

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'

class DoramasOnline:
    def __init__(self, url='https://doramasonline.org'):
        self.base = url if url.endswith('/') else url + '/'
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8',
            'Referer': self.base
        }

    def soup(self, html):
        return BeautifulSoup(html, 'html.parser')

    def _improve_image_quality(self, img_url):
        """
        Melhora a qualidade da imagem substituindo tamanhos baixos do TMDB por w780 (alta qualidade)
        """
        if not img_url or 'image.tmdb.org' not in img_url:
            return img_url
        
        # Padrões de tamanho do TMDB que podem estar na URL
        low_quality_patterns = [
            '/w92/', '/w154/', '/w185/', '/w342/', '/w500/',
            '/h632/', '/original/'
        ]
        
        # Substituir qualquer tamanho encontrado por w780 (alta qualidade)
        for pattern in low_quality_patterns:
            if pattern in img_url:
                img_url = img_url.replace(pattern, '/w780/')
                break
        
        return img_url

    def _clean_aviso_url(self, url):
        try:
            parsed = urlparse(url)
            if "doramasonline.org/aviso" in url and "url=" in parsed.query:
                qs = parse_qs(parsed.query)
                if "url" in qs:
                    return unquote(qs["url"][0])
        except:
            pass
        return url

    def _clean_stream(self, url):
        try:
            if '&img=' in url:
                url = url.split('&img=')[0]
            if '&poster=' in url:
                url = url.split('&poster=')[0]
        except:
            pass
        return url

    def _clean_streamlitch(self, url):
        if not url or 'litch.alibabacdn.net' not in url:
            return url
        
        url = url.replace('&', '&')
        
        if '&img=' in url:
            url = url.split('&img=', 1)[0]
        
        if '&poster=' in url:
            url = url.split('&poster=', 1)[0]
        
        url = url.rstrip('&').rstrip('?')
        
        return url

    def _decode_holuagency(self, url):
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)

            if "auth" not in qs:
                url = self._clean_streamlitch(url)
                url = self._clean_aviso_url(url)
                url = self._clean_stream(url)
                return url

            b64data = qs["auth"][0]
            while len(b64data) % 4 != 0:
                b64data += "="

            decoded = base64.b64decode(b64data).decode("utf-8")
            js = json.loads(decoded)

            real = js.get("url")
            if not real:
                url = self._clean_streamlitch(url)
                url = self._clean_aviso_url(url)
                url = self._clean_stream(url)
                return url

            real = self._clean_streamlitch(real)
            real = self._clean_aviso_url(real)
            real = self._clean_stream(real)
            
            return real

        except Exception:
            url = self._clean_streamlitch(url)
            url = self._clean_aviso_url(url)
            url = self._clean_stream(url)
            return url

    def scraper_dublados(self, page=1):
        url = f'{self.base}br/generos/dublado/page/{page}/'
        return self._scrape_catalogo(url)

    def scraper_legendados(self, page=1):
        url = f'{self.base}br/generos/legendado/page/{page}/'
        return self._scrape_catalogo(url)

    def scraper_filmes(self, page=1):
        url = f'{self.base}br/filmes/page/{page}/'
        return self._scrape_catalogo(url)

    def search_doramas(self, pesquisa):
        query = quote_plus(pesquisa)
        url = f'{self.base}/?s={query}'
        return self._scrape_busca(url)

    def scraper_episodios(self, url):
        episodios = []
        try:
            r = requests.get(url, headers=self.headers)
            soup = self.soup(r.text)

            serie_name = ''
            try:
                h1 = soup.select_one('div.data h1') or soup.select_one('.data h1')
                if h1 and h1.text:
                    serie_name = h1.text.strip()
            except:
                serie_name = ''

            temporadas = soup.select('div.se-c')

            if temporadas:
                for temporada in temporadas:
                    nome_temp_raw = temporada.select_one('div.se-q span.se-t')
                    temp_txt = nome_temp_raw.text.strip() if nome_temp_raw else ''

                    temp_num = re.findall(r'\d+', temp_txt)
                    season_num = temp_num[0] if temp_num else '1'

                    lista = temporada.select('ul.episodios > li')

                    for idx, li in enumerate(lista, start=1):
                        a = li.select_one('.episodiotitle a')
                        img = li.select_one('.imagen img')

                        if not a:
                            continue

                        num_div = li.select_one('.numerando')
                        ep_num = ''

                        if num_div and num_div.text:
                            nums = re.findall(r'\d+', num_div.text)
                            if len(nums) >= 2:
                                season_num = nums[0]
                                ep_num = nums[1]
                            elif len(nums) == 1:
                                ep_num = nums[0]
                        else:
                            nums = re.findall(r'\d+', a.text)
                            if nums:
                                ep_num = nums[-1]
                            else:
                                ep_num = str(idx)

                        ep_title_text = a.text.strip()

                        if season_num and ep_num:
                            se_part = f"S{season_num}E{ep_num}"
                        else:
                            se_part = f"T{season_num} - Ep{ep_num}".strip()

                        if serie_name:
                            full_title = f"{serie_name} - {se_part}"
                        else:
                            full_title = f"{se_part} - {ep_title_text}"

                        link = a.get('href', '').strip()
                        thumb = img.get('src', '').strip() if img else ''
                        thumb = self._improve_image_quality(thumb)

                        episodios.append((full_title, link, thumb, url))

            else:
                lista = (
                    soup.select('ul.episodios > li')
                    or soup.select('div.episodios li')
                    or soup.find_all('li')
                )

                for li in lista:
                    a = li.select_one('.episodiotitle a') or li.find('a')
                    img = li.select_one('.imagen img')

                    if not a:
                        continue

                    num_div = li.select_one('.numerando')
                    season_num = ''
                    ep_num = ''

                    if num_div and num_div.text:
                        nums = re.findall(r'\d+', num_div.text)
                        if len(nums) >= 2:
                            season_num, ep_num = nums[0], nums[1]
                        elif len(nums) == 1:
                            ep_num = nums[0]

                    if not ep_num:
                        nums = re.findall(r'\d+', a.text)
                        if nums:
                            ep_num = nums[-1]

                    if not season_num:
                        season_num = '1'

                    ep_title_text = a.text.strip()
                    se_part = f"S{season_num}E{ep_num}" if ep_num else f"T{season_num}"

                    if serie_name:
                        full_title = f"{serie_name} - {se_part} - {ep_title_text}"
                    else:
                        full_title = f"{se_part} - {ep_title_text}"

                    link = a.get('href', '').strip()
                    thumb = img.get('src', '').strip() if img else ''
                    thumb = self._improve_image_quality(thumb)

                    episodios.append((full_title, link, thumb, url))

        except Exception:
            pass

        return episodios

    def scraper_players(self, url):
        opcoes = []
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = self.soup(r.text)

            nomes_por_nume = {}
            for li in soup.select('ul#playeroptionsul li.dooplay_player_option'):
                try:
                    nume = (li.get('data-nume') or '').strip()
                    name_el = li.find('span', {'class': 'title'})
                    name = (name_el.text or '').strip() if name_el else f'Opção {nume or "?"}'
                    if nume:
                        nomes_por_nume[nume] = name
                except:
                    continue

            for box in soup.select('#dooplay_player_content .source-box'):
                box_id = box.get('id', '')
                m = re.search(r'source-player-(\d+)', box_id or '')
                nume = m.group(1) if m else None

                a = box.find('a', href=True)
                if a and a.get('href'):
                    raw = a['href'].strip()
                    link = self._decode_holuagency(raw)
                    name = nomes_por_nume.get(nume, f'Opção {nume}') if nume else 'Opção'
                    opcoes.append((name, link))
                    continue

                iframe = box.find('iframe', src=True)
                if iframe:
                    raw = iframe['src'].strip()
                    link = self._decode_holuagency(raw)
                    name = nomes_por_nume.get(nume, f'Opção {nume}') if nume else 'Opção'
                    opcoes.append((name, link))

            if not opcoes:
                iframes = soup.find_all("iframe", src=True)
                for n, iframe in enumerate(iframes, start=1):
                    raw = iframe.get("src", "").strip()
                    link = self._decode_holuagency(raw)
                    name = f"Opção {n}"
                    opcoes.append((name, link))

        except Exception:
            pass

        return opcoes

    def _scrape_catalogo(self, url):
        itens = []
        next_page = False
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = self.soup(r.text)

            container = soup.find("div", class_=lambda x: x and x.startswith("items")) \
                        or soup.find("div", {"id": "box_movies"}) \
                        or soup.find("div", class_="items") \
                        or soup

            artigos = container.find_all("article", id=lambda x: x and x.startswith("post")) \
                      or container.find_all("div", class_="movie-item") \
                      or container.find_all("div", class_="item")

            for art in artigos:
                try:
                    a = art.find("a")
                    href = a.get("href", "") if a else ""
                    title_tag = art.find("h3") or a
                    title = title_tag.text.strip() if title_tag else href
                    img = (art.find("img").get("src", "") if art.find("img") else "")
                    img = self._improve_image_quality(img)
                    itens.append((title, href, img, title, url))
                except:
                    continue

            current_page = 1
            m_current = re.search(r'/page/(\d+)', url)
            if m_current:
                try:
                    current_page = int(m_current.group(1))
                except:
                    current_page = 1

            if itens:
                next_page = current_page + 1

        except Exception:
            pass

        return itens, next_page

    def _scrape_busca(self, url):
        itens = []
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = self.soup(r.text)

            results = soup.find_all("div", class_="result-item") \
                      or soup.find_all("article", id=lambda x: x and x.startswith("post")) \
                      or soup.find_all("div", class_="items")

            for res in results:
                try:
                    a = res.find("a")
                    href = a.get("href", "") if a else ""
                    title_tag = res.find("div", class_="title") or res.find("h3") or a
                    title = title_tag.text.strip() if title_tag else href
                    img = (res.find("img").get("src", "") if res.find("img") else "")
                    img = self._improve_image_quality(img)
                    itens.append((title, href, img, title, self.base))
                except:
                    continue

        except Exception:
            pass

        return itens
