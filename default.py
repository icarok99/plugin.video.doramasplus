# -*- coding: utf-8 -*-
from lib.helper import *
from lib.doramas import DoramasOnline
from lib.resolver import Resolver
from lib.proxy import get_proxy

scraper = DoramasOnline('https://doramasonline.org')
resolver = Resolver()
proxy = get_proxy()

if not exists(profile):
    try:
        os.mkdir(profile)
    except:
        pass

try:
    class Donate_(xbmcgui.WindowDialog):
        def __init__(self):
            try:
                self.image = xbmcgui.ControlImage(440, 128, 400, 400, translate(os.path.join(homeDir, 'resources', 'images','qrcode-pix.png')))
                self.text = xbmcgui.ControlLabel(x=210,y=570,width=1100,height=25,label='[B][COLOR pink]SE ESSE ADD-ON LHE AGRADA, FAÇA UMA DOAÇÃO VIA PIX ACIMA E MANTENHA ESSE SERVIÇO ATIVO[/COLOR][/B]',textColor='pink')
                self.text2 = xbmcgui.ControlLabel(x=495,y=600,width=1000,height=25,label='[B][COLOR pink]PRESSIONE VOLTAR PARA SAIR[/COLOR][/B]',textColor='pink')
                self.addControl(self.image)
                self.addControl(self.text)
                self.addControl(self.text2)
            except:
                pass
except:
    pass

def donate_question():
    q = yesno('', 'Deseja fazer uma doação ao desenvolvedor?', nolabel='NÃO', yeslabel='SIM')
    if q:
        dialog2('AVISO', 'A DOAÇÃO É UMA AJUDA AO DESENVOLVEDOR PARA MANTER O ADD-ON ATIVO!')
        dialog_donate = Donate_()
        dialog_donate.doModal()

def get_autoplay_setting():
    try:
        setting_value = addon.getSetting('autoplay')
        return setting_value == 'true'
    except Exception as e:
        log(f'Erro ao ler configuração autoplay: {e}')
        return False

@route('/')
def index():
    setcontent('videos')
    addMenuItem({
        'name': 'PESQUISAR DORAMA',
        'description': '[B]Pesquise doramas pelo nome[/B]',
        'iconimage': translate(os.path.join(homeDir, 'resources', 'images','search.jpg'))
    }, destiny='/doramassearch')
    
    addMenuItem({
        'name': 'DORAMAS DUBLADOS',
        'description': '[B]Assista os melhores doramas dublados[/B]',
        'iconimage': translate(os.path.join(homeDir, 'resources', 'images','doramas dub.jpg'))
    }, destiny='/doramas_dublados')
    
    addMenuItem({
        'name': 'DORAMAS LEGENDADOS',
        'description': '[B]Assista os melhores doramas legendados[/B]',
        'iconimage': translate(os.path.join(homeDir, 'resources', 'images','doramas leg.jpg'))
    }, destiny='/doramas_legendados')
    
    addMenuItem({
        'name': 'CONFIGURAÇÕES',
        'description': '[B]Área de configuração[/B]',
        'iconimage': translate(os.path.join(homeDir, 'resources', 'images','settings.jpg'))
    }, destiny='/settings')

    addMenuItem({
        'name': 'DOAÇÃO',
        'description': '[B]Área de doação[/B]',
        'iconimage': translate(os.path.join(homeDir, 'resources', 'images','donate.jpg'))
    }, destiny='/donate')
    
    end()

@route('/donate')
def donate(param):
    donate_question()

@route('/settings')
def settings(param):
    addon.openSettings()

@route('/doramassearch')
def doramassearch(param):
    search = input_text(heading='Pesquisar Dorama')
    if search:
        itens = scraper.search_doramas(search)
        if itens:
            setcontent('tvshows')
            for title, href, img, _, _ in itens:
                addMenuItem({
                    'name': title,
                    'description': '',
                    'iconimage': img,
                    'url': href
                }, destiny='/episodios')
            end()
        else:
            notify('Nenhum resultado encontrado')

@route('/doramas_dublados')
def doramas_dublados(param):
    try:
        page = int(param.get('page', 1))
    except:
        page = 1
    
    itens, next_page = scraper.scraper_dublados(page=page)
    
    if itens:
        setcontent('tvshows')
        for title, href, img, _, _ in itens:
            addMenuItem({
                'name': title,
                'description': '',
                'iconimage': img,
                'url': href,
                'prioridade': 'DUBLADO'
            }, destiny='/episodios')
        
        if next_page:
            addMenuItem({
                'name': f'Página {next_page}',
                'description': '',
                'iconimage': translate(os.path.join(homeDir, 'resources', 'images','next.jpg')),
                'page': next_page
            }, destiny='/doramas_dublados')
        
        end()
    else:
        notify('Nenhum dorama disponível')

@route('/doramas_legendados')
def doramas_legendados(param):
    try:
        page = int(param.get('page', 1))
    except:
        page = 1
    
    itens, next_page = scraper.scraper_legendados(page=page)
    
    if itens:
        setcontent('tvshows')
        for title, href, img, _, _ in itens:
            addMenuItem({
                'name': title,
                'description': '',
                'iconimage': img,
                'url': href,
                'prioridade': 'LEGENDADO'
            }, destiny='/episodios')
        
        if next_page:
            addMenuItem({
                'name': f'Página {next_page}',
                'description': '',
                'iconimage': translate(os.path.join(homeDir, 'resources', 'images','next.jpg')),
                'page': next_page
            }, destiny='/doramas_legendados')
        
        end()
    else:
        notify('Nenhum dorama disponível')

@route('/episodios')
def episodios(param):
    url = param.get("url", "")
    prioridade = param.get("prioridade", "")
    name = param.get("name", "")
    iconimage = param.get("iconimage", "")
    
    if not url:
        return
    
    if '/filmes/' in url:
        addMenuItem({
            'name': name,
            'iconimage': iconimage,
            'url': url,
            'prioridade': prioridade,
            'playable': 'true'
        }, destiny='/opcoes', folder=False)
        end()
        return
    
    try:
        import requests
        r = requests.get(url, headers=scraper.headers, timeout=10)
        soup = scraper.soup(r.text)
        if soup.find('ul', {'id': 'playeroptionsul'}):
            addMenuItem({
                'name': name,
                'iconimage': iconimage,
                'url': url,
                'prioridade': prioridade,
                'playable': 'true'
            }, destiny='/opcoes', folder=False)
            end()
            return
    except:
        pass
    
    lista_episodios = scraper.scraper_episodios(url)
    if lista_episodios:
        setcontent('episodes')
        for title, link, img, _ in lista_episodios:
            addMenuItem({
                'name': title,
                'iconimage': img,
                'url': link,
                'prioridade': prioridade,
                'playable': 'true'
            }, destiny='/opcoes', folder=False)
        end()
    else:
        notify('Nenhum episódio encontrado')

@route('/opcoes')
def opcoes(param):
    name = param.get("name", "Doramas")
    url = param.get("url", "")
    iconimage = param.get("iconimage", "")
    description = param.get("description", "")
    prioridade = param.get("prioridade", "").upper()
    playable = param.get("playable", "false")
    
    if not url:
        return
    
    op = scraper.scraper_players(url)
    
    if not op:
        notify('NENHUMA OPÇÃO DE PLAYER DISPONÍVEL')
        return
    
    autoplay_enabled = get_autoplay_setting()
    
    if autoplay_enabled:
        notify('AGUARDE...')
        
        players_para_tentar = op
        if prioridade:
            players_prioritarios = [(nome, link) for nome, link in op 
                                   if nome.upper().startswith(prioridade)]
            
            if players_prioritarios:
                players_para_tentar = players_prioritarios
        
        for nome_player, page_url in players_para_tentar:
            try:
                stream, sub = resolver.resolverurls(page_url, url)
                
                if stream:
                    stream_proxy = proxy.get_proxy_url(stream)
                    
                    play_video({
                        'url': stream_proxy,
                        'sub': sub,
                        'name': name,
                        'iconimage': iconimage,
                        'description': description,
                        'playable': playable
                    })
                    return
            except Exception as e:
                continue
        
        notify('NENHUM PLAYER FUNCIONOU')
        return
    
    else:
        if prioridade:
            op_filtradas = [(nome, link) for nome, link in op 
                           if nome.upper().startswith(prioridade)]
            
            if op_filtradas:
                op = op_filtradas
        
        items_options = [option for option, link in op]
        
        try:
            op2 = select('SELECIONE UMA OPÇÃO:', items_options)
        except:
            op2 = 0
        
        if op2 >= 0:
            notify('AGUARDE...')
            page = op[op2][1]
            
            stream, sub = resolver.resolverurls(page, url)
            
            if stream:
                stream_proxy = proxy.get_proxy_url(stream)
                
                play_video({
                    'url': stream_proxy,
                    'sub': sub,
                    'name': name,
                    'iconimage': iconimage,
                    'description': description,
                    'playable': playable
                })
            else:
                notify('STREAM INDISPONÍVEL, TENTE OUTRO PLAYER')
