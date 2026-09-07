#!/usr/bin/env python3
"""Build a human-readable Ukrainian vinyl catalogue from Discogs scrape JSON."""
import json, re, sys
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from pathlib import Path

from expanded_research import research

_commons_cache = {}


def stable_image_url(url):
    """Use a clean Wikimedia thumbnail URL without tracking/query parameters."""
    clean = (url or '').split('?', 1)[0]
    match = re.match(r'https?://(?:upload|thumb)\.wikimedia\.org/wikipedia/([^/]+)/(.+)$', clean)
    if not match:
        return clean
    namespace, rest = match.groups()
    parts = rest.split('/')
    if parts and parts[0] == 'thumb':
        original_parts = parts[1:-1]
        filename = parts[-2] if len(parts) >= 2 else ''
    else:
        filename = parts[-1]
        original_parts = parts[:-1] + [filename]
    if len(original_parts) >= 2 and filename:
        return 'https://thumb.wikimedia.org/wikipedia/' + namespace + '/thumb/' + '/'.join(original_parts) + '/330px-' + filename
    return clean


def commons_period_photo(artist, period):
    """Find one period-appropriate Commons image, without guessing when none exists."""
    clean_artist = re.sub(r'[()*]', '', artist).replace('/', ' ').strip()
    if not clean_artist or clean_artist.lower() in {'various', 'unknown artist'}:
        return None
    if clean_artist.lower() in {'karna', 'colosseum', 'blondie', 'soul media', 'the alan parsons project'}:
        return None
    artist_tokens = [token for token in re.findall(r'[a-zа-яіїєґ]{4,}', clean_artist.lower()) if token not in {'the', 'and', 'his', 'with', 'yes', 'police', 'band', 'group', 'orchestra', 'project'}]
    if not artist_tokens:
        return None
    cache_key = (clean_artist, str(period))
    if cache_key in _commons_cache:
        return _commons_cache[cache_key]
    year_match = re.search(r'\b(19|20)\d{2}\b', str(period))
    year = year_match.group(0) if year_match else ''
    queries = [
        f'{clean_artist} {year} photo'.strip(),
        f'{clean_artist} portrait photo',
        f'{clean_artist} live concert photo',
    ]
    result = None
    rejected = ('album cover', 'single cover', 'logo', 'poster', 'record cover', 'discography', '.pdf', '.png', '.svg', 'train', 'pram', 'ferrari', 'guitar', 'stratocaster', 'fender', 'martin', 'museum', 'colosseo', 'billboard')
    accepted = ('photo', 'portrait', 'concert', 'live', 'stage', 'studio', 'publicity', 'press')
    try:
        for query in queries:
            params = urlencode({
                'action': 'query', 'generator': 'search', 'gsrsearch': query,
                'gsrnamespace': 6, 'gsrlimit': 5, 'prop': 'imageinfo',
                'iiprop': 'url|extmetadata', 'iiurlwidth': 900,
                'format': 'json', 'origin': '*',
            })
            req = Request(
                'https://commons.wikimedia.org/w/api.php?' + params,
                headers={'User-Agent': 'vinyl-catalogue/1.0'},
            )
            payload = json.load(urlopen(req, timeout=12))
            pages = payload.get('query', {}).get('pages', {})
            candidates = list(pages.values())
            candidates.sort(key=lambda p: any(word in p.get('title', '').lower() for word in accepted), reverse=True)
            for page in candidates:
                title = (page or {}).get('title', '').removeprefix('File:')
                title_lower = title.lower()
                if any(word in title_lower for word in rejected):
                    continue
                token_matches = [token.rstrip('s')[:5] in title_lower for token in artist_tokens]
                if artist_tokens and (not any(token_matches) or (len(artist_tokens) > 1 and not all(token_matches))):
                    continue
                if year:
                    title_years = [int(value) for value in re.findall(r'\b(?:19|20)\d{2}\b', title)]
                    if title_years and min(abs(int(year) - value) for value in title_years) > 10:
                        continue
                if query != queries[0] and not any(word in title_lower for word in accepted):
                    continue
                info = (page or {}).get('imageinfo', [{}])[0]
                image_url = info.get('thumburl') or info.get('url')
                if image_url and title:
                    result = {
                        'image': stable_image_url(image_url),
                        'page': 'https://commons.wikimedia.org/wiki/File:' + quote(title.replace(' ', '_')),
                        'title': title,
                    }
                    break
            if result:
                break
    except Exception:
        result = None
    if result is None:
        try:
            wiki_artist = clean_artist.split(' / ')[0].strip()
            endpoint = 'https://en.wikipedia.org/api/rest_v1/page/summary/' + quote(wiki_artist.replace(' ', '_'))
            req = Request(endpoint, headers={'User-Agent': 'vinyl-catalogue/1.0'})
            summary = json.load(urlopen(req, timeout=12))
            image_url = ((summary.get('thumbnail') or {}).get('source') or '').split('?', 1)[0]
            if any(word in image_url.lower() for word in ('billboard', 'ferrari', 'guitar', 'stratocaster', 'fender', 'colosseo', 'pram', 'train')):
                image_url = ''
            page_title = summary.get('title', wiki_artist)
            page_title_lower = page_title.lower()
            page_token_matches = [token.rstrip('s')[:5] in page_title_lower for token in artist_tokens]
            if image_url and (not artist_tokens or (any(page_token_matches) and (len(artist_tokens) == 1 or all(page_token_matches)))):
                result = {
                    'image': stable_image_url(image_url),
                    'page': summary.get('content_urls', {}).get('desktop', {}).get('page') or 'https://en.wikipedia.org/wiki/' + quote(page_title.replace(' ', '_')),
                    'title': page_title,
                }
        except Exception:
            result = None
    if result is None:
        try:
            params = urlencode({
                'action': 'query', 'list': 'search', 'srsearch': clean_artist,
                'srnamespace': 0, 'srlimit': 1, 'format': 'json', 'origin': '*',
            })
            req = Request(
                'https://en.wikipedia.org/w/api.php?' + params,
                headers={'User-Agent': 'vinyl-catalogue/1.0'},
            )
            search_payload = json.load(urlopen(req, timeout=12))
            hit = next(iter(search_payload.get('query', {}).get('search', [])), None)
            if hit:
                params = urlencode({
                    'action': 'query', 'pageids': hit['pageid'],
                    'prop': 'pageimages|info', 'piprop': 'thumbnail',
                    'pithumbsize': 900, 'inprop': 'url',
                    'format': 'json', 'origin': '*',
                })
                req = Request(
                    'https://en.wikipedia.org/w/api.php?' + params,
                    headers={'User-Agent': 'vinyl-catalogue/1.0'},
                )
                pages = json.load(urlopen(req, timeout=12)).get('query', {}).get('pages', {})
                page = next(iter(pages.values()), None)
                image_url = ((page or {}).get('thumbnail') or {}).get('source')
                page_title_lower = (page or {}).get('title', '').lower()
                page_token_matches = [token.rstrip('s')[:5] in page_title_lower for token in artist_tokens]
                if image_url and (not artist_tokens or (any(page_token_matches) and (len(artist_tokens) == 1 or all(page_token_matches)))):
                    result = {
                        'image': stable_image_url(image_url),
                        'page': (page or {}).get('fullurl') or 'https://en.wikipedia.org/wiki/' + quote((page or {}).get('title', '').replace(' ', '_')),
                        'title': (page or {}).get('title', clean_artist),
                    }
        except Exception:
            result = None
    _commons_cache[cache_key] = result
    return result

facts = {
0: dict(created="2026", story="KARNA переосмислила відомі пісні в акустичнішому, камерному й атмосферному форматі — це радше нова глава гурту, ніж просто unplugged-збірка. Видання Carpathian Mist має 99 примірників, що робить саме цей варіант особливо колекційним.", tracks="Мама Галичина; Моя Мила; Чорна Скрипка", links=["https://tt-records.com.ua/karna-persa-karpatska-simfoniia"]),
1: dict(created="2025", story="Альбом поєднує інді-рок, речитатив і дуже локальну львівську образність. Важлива особливість — участь Христини Соловій і звернення до поезії Максима Кривцова у «На Дорогах», що надає платівці виразного воєнного й особистого контексту.", tracks="На Дорогах; Холодна Кров; Ангедонія", links=["https://music.apple.com/us/album/%D0%BC%D0%B0%D1%88%D0%B8%D0%BD%D0%B0-%D0%B4%D0%BB%D1%8F-%D1%82%D1%80%D0%B0%D0%BD%D1%81%D0%BB%D1%8F%D1%86%D1%96%D1%97-%D1%81%D0%BD%D1%96%D0%B2/1811384210"]),
2: dict(created="2026", story="Свіжий український поп-панк-реліз, який варто слухати як авторський коментар до сьогодення, а не як буквальну “збірку хітів”. У назвах треків уже закладено сильний портрет епохи — від «Атеїстки Богуслави» до «Краще, що сталось за цю війну».", tracks="Атеїстка Богуслава; Краще, що сталось за цю війну; 2007", links=["https://music.apple.com/us/artist/%D1%83%D0%BB%D1%8F%D0%BD%D0%B0-%D0%B4%D0%B5%D0%BB%D1%8C-%D1%80%D0%B5%D0%B9/1609434365"]),
3: dict(created="1979", story="Четвертий студійний альбом The Alan Parsons Project. Його концептуальне ядро — напруження між чоловічим і жіночим поглядом; продюсерсько-інженерна педантичність Алана Парсонса тут поєднана з великою кількістю запрошених вокалістів. Паралельно з ним записували експериментальний, довго невиданий матеріал The Sicilian Defence.", tracks="Lucifer; Damned If I Do; Don't Hold Back", links=["https://www.the-alan-parsons-project.com/eve", "https://en.wikipedia.org/wiki/Eve_(Alan_Parsons_Project_album)"]),
4: dict(created="1982–1983", story="Ключовий альбом повернення Yes. Матеріал починали записувати як проєкт Cinema з Тревором Рабіном, а повернення Джона Андерсона й Тоні Кея перетворило його на нову версію Yes. Саунд став коротшим, гучнішим і значно більш радіоформатним, але зберіг складні аранжування.", tracks="Owner Of A Lonely Heart; Cinema; Leave It", links=["https://www.rhino.com/aod/90125-yes-0", "https://en.wikipedia.org/wiki/90125"]),
5: dict(created="1980", story="Пізній і нині дуже цінований японський jazz-funk Soul Media. Це останній студійний альбом Soul Media; Jiro Inagaki поєднав теплий саксофон із пружною ритм-секцією й диско-фанковою ясністю, тому платівка однаково цікава і джазовим слухачам, і crate-diggers.", tracks="Memory Lane; Rain; Double Images", links=["https://www.onigiri-records.com/release/26084674/soul-media-memory-lane", "https://jazzprofiles.com/profile/ja-jiro-inagaki/"]),
6: dict(created="1981", story="The Police записували альбом на Montserrat і в Канаді, розширюючи тріо синтезаторами, саксофонами й більш студійною фактурою. Це момент, коли панк-реггі-енергія ранніх Police остаточно переросла у складний new wave-поп.", tracks="Every Little Thing She Does Is Magic; Invisible Sun; Spirits In The Material World", links=["https://en.wikipedia.org/wiki/Ghost_in_the_Machine_(The_Police_album)"]),
7: dict(created="1938–1942", story="Це компіляція, а не альбом, записаний у 1982 році: на платівці зібрані оригінальні записи епохи Glenn Miller. Її цінність — у “кристалічному” big-band саунді, чітких рифах секції саксофонів і вокальних номерах Tex Beneke та The Modernaires.", tracks="In The Mood; Moonlight Serenade; Chattanooga Choo Choo", links=["https://en.wikipedia.org/wiki/Glenn_Miller"]) ,
8: dict(created="1972", story="Під чеською назвою «Na Samém Kraji Útesu» заховано чехословацький клубний пресинг Close To The Edge. Оригінал — один із канонічних прог-рок альбомів: довгі композиції будуються як багаточастинні сюїти, а Білл Бруфорд залишив Yes невдовзі після запису.", tracks="Close To The Edge; And You And I; Siberian Khatru", links=["https://en.wikipedia.org/wiki/Close_to_the_Edge"]),
9: dict(created="2024–2025", story="Другий студійний альбом The Last Dinner Party розвиває їхній бароковий, театральний indie-rock у темнішому напрямку. За дискогс-кредитами, аранжування підсилюють струнні, духові та хорова драматургія — це платівка, яку цікаво слухати як сценічну виставу без сцени.", tracks="Agnus Dei; Second Best; The Scythe; Inferno", links=["https://en.wikipedia.org/wiki/The_Last_Dinner_Party"]),
10: dict(created="1978", story="Концептуальний альбом про єгипетські піраміди, пам’ять і людську одержимість безсмертям. Парсонс особливо ефектно балансує між оркестровим прог-роком, синтезаторами й майже кінематографічними інструментальними переходами.", tracks="Voyager; Pyramania; Hyper-Gamma-Spaces", links=["https://en.wikipedia.org/wiki/Pyramid_(The_Alan_Parsons_Project_album)"]),
11: dict(created="1980", story="Один із найцілісніших концептуальних альбомів APP: тема азарту й випадку розгортається від «Games People Play» до великої сюїти заголовної композиції. Пісня «Time» стала одним із найвиразніших вокальних моментів проєкту.", tracks="Games People Play; Time; The Turn Of A Friendly Card", links=["https://en.wikipedia.org/wiki/The_Turn_of_a_Friendly_Card"]),
12: dict(created="2020–2021", story="Платівка, що зафіксувала перехід Måneskin від клубної римської групи до міжнародного явища: після перемоги на Sanremo й Eurovision «Zitti E Buoni» став її символом. Тут глем, хард-рок і сучасний поп працюють як один дуже прямий концертний жест.", tracks="Zitti E Buoni; Coraline; I Wanna Be Your Slave", links=["https://en.wikipedia.org/wiki/Teatro_d%27ira:_Vol._I"]),
13: dict(created="1970–1971", story="Перший альбом, де Linda McCartney офіційно стала співавторкою й учасницею гурту Paul. Після розпаду The Beatles Пол записував його як дуже домашню, але амбітну заяву про нове життя; «Too Many People» містить шпильку в бік Джона Леннона, а «Uncle Albert / Admiral Halsey» показує його любов до монтажу мініатюр.", tracks="Too Many People; Uncle Albert / Admiral Halsey; The Back Seat Of My Car", links=["https://en.wikipedia.org/wiki/Ram_(Paul_and_Linda_McCartney_album)"]),
14: dict(created="1973", story="The New England Conservatory Ragtime Ensemble під керуванням Gunther Schuller зробив із музики Scott Joplin не музейний експонат, а живий ансамблевий репертуар. «The Entertainer» тут подано двічі — як нагадування, наскільки по-різному може дихати одна й та сама тема.", tracks="The Entertainer; Maple Leaf Rag; The Cascades", links=["https://en.wikipedia.org/wiki/The_Red_Back_Book"]),
15: dict(created="1970–1983", story="Східнонімецька AMIGA-компіляція, яка проводить слухача через різні фази Clapton: від блюз-року до м’якшого поп-року. Цікава саме як культурний артефакт: західна рок-музика потрапляла за Залізну завісу через локальні ліцензійні збірки.", tracks="Lay Down Sally; After Midnight; I Shot The Sheriff", links=["https://en.wikipedia.org/wiki/Eric_Clapton_(album)"]),
16: dict(created="1975–1976", story="Дебютний концептуальний альбом APP за оповіданнями й поезією Edgar Allan Poe. «The Raven» став одним із ранніх прикладів використання вокодера як художнього голосу, а «The Fall Of The House Of Usher» — розгорнутою симфонічною сюїтою.", tracks="The Raven; The Tell-Tale Heart; The Fall Of The House Of Usher", links=["https://en.wikipedia.org/wiki/Tales_of_Mystery_and_Imagination_(album)"]),
17: dict(created="1975–1976", story="Це інший німецький пресинг того самого Poe-альбому, вже як репрес/стерео-гейтфолд. Для прослуховування важливо пам’ятати: рік на конверті — 1978, але композиції та студійна робота належать першій половині 1970-х.", tracks="The Raven; The Cask Of Amontillado; To One In Paradise", links=["https://www.the-alan-parsons-project.com/"]),
18: dict(created="1977", story="Другий альбом APP розмірковує про людину й машину, але не є буквальним саундтреком до Asimov — це автономна інтерпретація теми. «I Wouldn't Want To Be Like You» став хітом, а «The Voice» і «Breakdown» показують, як Парсонс перетворював студійні ефекти на частину композиції.", tracks="I Wouldn't Want To Be Like You; Breakdown; The Voice", links=["https://en.wikipedia.org/wiki/I_Robot_(album)"]),
19: dict(created="1979", story="Оригінальний Yeni Bir Gün — важливий альбом анатолійського року Barış Manço й Kurtalan Ekspres; ваш диск — пізніше турецьке перевидання 2018 року. На ньому традиційні мелодичні інтонації, психоделія й рок-аранжування працюють як єдина місцева мова.", tracks="Yeni Bir Gün; Sarı Çizmeli Mehmet Ağa; Ağlama Değmez Hayat", links=["https://en.wikipedia.org/wiki/Bar%C4%B1%C5%9F_Man%C3%A7o", "https://www.barismancomix.com/biyografi/index.php"]),
20: dict(created="1972–1973", story="Потрійний live-документ Yes із різних концертів і з двома барабанщиками в перехідний момент: Білл Бруфорд ще звучить на частині матеріалу, а Алан Вайт уже входить у склад. Альбом зберігає масштаб сцени краще за студійні платівки гурту.", tracks="Yours Is No Disgrace; Starship Trooper; Perpetual Change", links=["https://en.wikipedia.org/wiki/Yessongs"]),
21: dict(created="1935–1942", story="Ще одна компіляція оригінальних записів, цього разу з фокусом на оркестр Glenn Miller. Вона корисна як “контрольна точка” для слуху: чути, як до появи рок-ритму поп-музика могла бути одночасно танцювальною, оркестровою й надзвичайно точно аранжованою.", tracks="Moonlight Serenade; In The Mood; American Patrol", links=["https://en.wikipedia.org/wiki/Glenn_Miller"]) ,
22: dict(created="1976–1977", story="Low — перша частина Berlin Trilogy, хоча значну частину основ записували у Франції та Лос-Анджелесі, а завершували в Hansa Studios. Перша сторона — короткі, ламані пісні; друга — інструментальні ambient-пейзажі Eno/Visconti.", tracks="Sound And Vision; Warszawa; Be My Wife", links=["https://hansastudios.de/de/history/", "https://en.wikipedia.org/wiki/Low_(David_Bowie_album)"]),
23: dict(created="1983", story="Саундтрек до продовження Saturday Night Fever, для якого Sylvester Stallone запросив Bee Gees повернутися до диско-формули. На відміну від оригіналу, він сильніше прив’язаний до монтажу танцювальних сцен і до великого поп-звуку початку 1980-х.", tracks="Far From Over; The Woman In You; Staying Alive", links=["https://en.wikipedia.org/wiki/Staying_Alive_(soundtrack)"]),
24: dict(created="1977", story="Другий альбом Blondie ще має сирий нью-йоркський new-wave нерв, але вже демонструє майбутній поп-хист гурту. «Denis» — їхній проривний сингл у Європі; «(I'm Always Touched By Your) Presence, Dear» показує, як гурт умів зробити хіт із дивної, майже панкової фактури.", tracks="Denis; X Offender; Presence, Dear", links=["https://en.wikipedia.org/wiki/Plastic_Letters"]),
25: dict(created="1982–1983", story="David Bowie свідомо змінив курс у бік великого танцювального попу: Nile Rodgers, музиканти Chic і запис у Power Station дали платівці глянцевий, але живий groove. Це один із найуспішніших Bowie-релізів і важливий міст між арт-роком та MTV-естетикою.", tracks="Let's Dance; Modern Love; China Girl", links=["https://en.wikipedia.org/wiki/Let%27s_Dance_(David_Bowie_album)"]),
26: dict(created="1982", story="Для Thriller Quincy Jones і Michael Jackson будували платівку як послідовність потенційних синглів: з дев’яти треків сім потрапили в американський Top 10. У «Beat It» гітарне соло зіграв Eddie Van Halen, а Vincent Price додав голос до титульного треку.", tracks="Billie Jean; Beat It; Thriller", links=["https://www.loc.gov/static/programs/national-recording-preservation-board/documents/QuincyJonesInterview.pdf", "https://en.wikipedia.org/wiki/Thriller_(album)"]),
27: dict(created="1972–1973", story="Pink Floyd майже рік обкатували матеріал наживо до завершення студійної версії. Запис проходив у Abbey Road зі staff engineer Alan Parsons; касові петлі в «Money», EMS-ефекти в «On The Run», хор Clare Torry та голоси випадкових співрозмовників зробили альбом лабораторією студійного звуку.", tracks="Time; The Great Gig In The Sky; Money", links=["https://www.abbeyroad.com/news/the-dark-side-of-the-moon-studio-documents-3299", "https://www.pinkfloyd.com/albums/the-dark-side-of-the-moon/", "https://en.wikipedia.org/wiki/The_Dark_Side_of_the_Moon"]),
28: dict(created="1985–1986", story="Madonna назвала True Blue найособистішим на той момент альбомом; у ньому поєднались романтичні пісні, латиноамериканські барви й соціально гострий «Papa Don't Preach». «Live To Tell» демонструє її драматичнішу сторону, а «La Isla Bonita» — поп, побудований на уявленій іспанській атмосфері.", tracks="Papa Don't Preach; Live To Tell; La Isla Bonita", links=["https://en.wikipedia.org/wiki/True_Blue_(Madonna_album)"]),
29: dict(created="1970–1971", story="Colosseum Live — документ британського jazz-rock у моменті, коли концертна імпровізація була не прикрасою, а основною формою. Джон Гайсман, Клем Клемпсон і Кріс Фарлоу працюють на межі блюзу, прогу та важкого року.", tracks="Lost Angeles; Skellington; Walking In The Park", links=["https://en.wikipedia.org/wiki/Colosseum_Live"]),
30: dict(created="1981", story="Abacab показує Genesis у точці переходу від прог-року до більш лаконічного поп-року. Гурт записував його на власній студії The Farm і дозволив усім трьом основним авторам — Collins, Banks, Rutherford — приносити матеріал у значно вільнішій формі.", tracks="Abacab; No Reply At All; Me And Sarah Jane", links=["https://en.wikipedia.org/wiki/Abacab"]),
31: dict(created="1978–1979", story="The Wall виріс із відчуття відчуження Роджера Вотерса після концертної історії Pink Floyd. Bob Ezrin допоміг перетворити матеріал на драматургічно цілісну рок-оперу; гітарне соло Девіда Гілмора в «Comfortably Numb» стало одним із найвідоміших у каталозі гурту.", tracks="Another Brick In The Wall, Part II; Comfortably Numb; Hey You", links=["https://en.wikipedia.org/wiki/The_Wall"]),
32: dict(created="1982", story="Spliff виникли з уламків Nina Hagen Band і принесли в німецьку new wave-сцену важкий бас, синтезатори, реггі-відлуння та абсурдистський гумор. Назва 85555 перегукується з каталожним номером платівки — типовий для гурту жест, де дизайн і музика грають разом.", tracks="85555; Carbonara; Deja Vu", links=["https://en.wikipedia.org/wiki/Spliff_(band)"]),
33: dict(created="1980-ті", story="Це сингл, а не альбом: локалізований чехословацький рок-н-рольний номер і парний бік. Його цінність для колекції — у тому, як світовий rock'n'roll-код адаптували під місцевих виконавців і формат Supraphon.", tracks="Halabala Rock'n Roll; Moucha", links=["https://www.discogs.com/release/6473649-Viktor-Sodoma-A-Josef-Melen-Halabala-Rockn-Roll-Rockn-Roll-Is-King-Moucha"]),
34: dict(created="1981", story="Ще один 7-дюймовий сингл Supraphon, що фіксує пізню фазу чехословацького попу. Karel Gott умів робити з короткого формату радіохіт, а сторона B додає платівці характерний двопісенний “портрет епохи”.", tracks="Už Dávno Dal Jsem Ti Klíč; Vítr V Zádech Mám", links=["https://en.wikipedia.org/wiki/Karel_Gott"]),
35: dict(created="1979", story="Katapult був одним із найпомітніших чеських hard-rock гуртів, які грали просто, гучно й без прогової декоративності. «Blues» — зручний мініатюрний приклад їхньої прямої пісенної школи та локальної рок-сцени кінця 1970-х.", tracks="Katapult; Blues", links=["https://en.wikipedia.org/wiki/Katapult_(band)"]),
36: dict(created="1970", story="Waldemar Matuška стояв на перетині чеської естради, кантрі та кінообразу; цей mono-сингл зберігає саме ранню, компактну еру 45-ок. Контраст двох сторін добре показує, як Supraphon поєднував легку пісню й західні стилістичні запозичення.", tracks="Co Je Žito; In Vino Veritas", links=["https://en.wikipedia.org/wiki/Waldemar_Matu%C5%A1ka"]),
37: dict(created="1950-ті–1960-ті", story="Pure Gold — компіляція, а не окремий студійний альбом Elvis. Її слухають як короткий маршрут через ранній rockabilly, балади й пізніший поп; чехословацький Opus-пресинг додає релізу власний історичний шар.", tracks="Jailhouse Rock; Love Me Tender; Suspicious Minds", links=["https://en.wikipedia.org/wiki/Elvis_Presley"]),
38: dict(created="1955–1960-ті", story="Компіляція Chuck Berry виводить на перший план його роль автора гітарної мови рок-н-ролу: короткі куплети, “говорюча” гітара й тексти про підліткову мобільність. Для такого релізу важливіше слухати різницю між оригінальними рок-н-рольними синглами, ніж порядок пісень.", tracks="Maybellene; Roll Over Beethoven; Johnny B. Goode", links=["https://en.wikipedia.org/wiki/Chuck_Berry"]),
39: dict(created="1930-ті–1950-ті", story="Збірка Billie Holiday нагадує, що її сила була не у вокальній демонстративності, а в мікротаймінгу, тембрі й здатності зробити чужий текст особистим. Mono тут — не недолік, а відповідний історичний формат первинних записів.", tracks="Strange Fruit; God Bless The Child; Lover Man", links=["https://en.wikipedia.org/wiki/Billie_Holiday"]),
40: dict(created="11 квітня 1978", story="Johnny Cash записав концерт у празькому Lucerna; чехословацьке видання 1983 року є пізнішим пресингом історичного виступу, а не датою концерту. Сам факт концерту за Залізною завісою робить платівку документом культурного обміну, не лише country-live.", tracks="Folsom Prison Blues; I Still Miss Someone; Sunday Mornin' Comin' Down", links=["https://en.wikipedia.org/wiki/Koncert_v_Praze_(In_Prague_%E2%80%93_Live)"]),
41: dict(created="2024–2025", story="Radio Afrodita повертає музику Мертвого Півня у новий вініловий контекст. У треклисті поруч живуть українська поезія, народні мелодії, Жадан і класика української естради — тому платівка працює як міст між львівським роком, фольклором і сучасним культурним пам’ятанням.", tracks="Ой Марічко, Чичері; Панно Інно; Я Помру Від Застуди", links=["https://www.discogs.com/release/33448796-Martvyj-Piven-Radio-Afrodita"]),
42: dict(created="1988", story="Young Man Running продовжує м’який синт-поп/soft-rock період Corey Hart після «Sunglasses at Night». На відміну від найбільших хітів, альбом цікавий тим, як артист намагається розсунути підлітковий поп-образ у бік дорослішої, дорожньої пісні.", tracks="In Your Soul; Still In Love; Crossroad Caravan", links=["https://en.wikipedia.org/wiki/Corey_Hart"]),
43: dict(created="1969–1972 записи; 1990 компіляція", story="Мелодійний USSR-реліз-компіляція, а не новий альбом Deep Purple. Він показує, як західний hard rock циркулював у пізньорадянському просторі через ліцензійні й напівофіційні збірки; червоні лейбли та позначка unofficial — частина його історії.", tracks="Child In Time; Highway Star; Smoke On The Water", links=["https://en.wikipedia.org/wiki/Deep_Purple"]),
44: dict(created="1988", story="Delicate Sound Of Thunder — концертний документ туру A Momentary Lapse of Reason, де Pink Floyd знову працювали як великий сценічний ансамбль. Для радянського білого-лейблового пресингу важлива подвійність: глобальний стадіонний рок і локальна історія розповсюдження Мелодії.", tracks="Shine On You Crazy Diamond; Comfortably Numb; Run Like Hell", links=["https://en.wikipedia.org/wiki/Delicate_Sound_of_Thunder"]),
45: dict(created="18 березня 1965", story="Це запис історичного празького концерту Louis Armstrong у Lucerna — гастролі за Залізною завісою, що мали величезний культурний резонанс. Оригінальний LP з’явився пізніше, тому рік вашого чехословацького repress не слід плутати з датою виступу.", tracks="Hello Dolly; Mack The Knife; When The Saints Come Marchin' In", links=["https://www.louisarmstronghouse.org/virtual-exhibits/hallo-satchmo-60th-anniversary-celebration-of-louis-armstrongs-1965-tour-of-prague/", "https://vltava.rozhlas.cz/louis-armstrong-zive-v-praze-zaznam-koncertu-od-nehoz-uplynulo-60-let-9428618"]),
46: dict(created="2022–2023", story="Dead Club City — концептуальний поп-рок про вигадане місто й життя всередині нього. Nothing But Thieves тут розширюють гітарний звук синтезаторами та поп-структурами; «Welcome To The DCC» працює як вступний титр до всієї платівки.", tracks="Welcome To The DCC; Overcome; Tomorrow Is Closed", links=["https://en.wikipedia.org/wiki/Dead_Club_City"]),
47: dict(created="1970–1971", story="Ваш європейський 180-грамовий ремастер — сучасне перевидання безіменного четвертого альбому Led Zeppelin. Основу записували в Headley Grange з Rolling Stones Mobile Studio; барабани «When The Levee Breaks» стали хрестоматійним прикладом великого room-sound.", tracks="Black Dog; Stairway To Heaven; When The Levee Breaks", links=["https://www.ledzeppelin.com/event/january-11-1971", "https://en.wikipedia.org/wiki/Led_Zeppelin_IV"]),
48: dict(created="2012–2013", story="AM зібрав у компактний формат блюзові рифи, хіп-хопову повторюваність бітів і нічну атмосферу раннього рок-н-ролу. «Do I Wanna Know?» та «R U Mine?» стали не просто синглами, а новою сценічною ідентичністю Arctic Monkeys.", tracks="Do I Wanna Know?; R U Mine?; Why'd You Only Call Me When You're High?", links=["https://en.wikipedia.org/wiki/AM_(Arctic_Monkeys_album)"]),
49: dict(created="1958", story="Come Fly With Me задуманий як музична подорож світом: Billy May аранжує пісні так, щоб кожна зупинка мала свій колір і ритм. Ваш синій європейський reissue — сучасний артефакт, але матеріал належить до золотого Capitol-періоду Sinatra.", tracks="Come Fly With Me; I've Got You Under My Skin; Chicago", links=["https://en.wikipedia.org/wiki/Come_Fly_with_Me_(Frank_Sinatra_album)"]),
50: dict(created="1950-ті", story="Збірка хітів Bill Haley & His Comets працює як короткий вступ до масового rock'n'roll: танцювальна четвірка, саксофон, slapback-відчуття й пісні, що перетворили молодіжну культуру на окремий ринок. Югославський пресинг додає східноєвропейський маршрут розповсюдження.", tracks="Rock Around The Clock; See You Later Alligator; Shake, Rattle & Roll", links=["https://en.wikipedia.org/wiki/Bill_Haley_%26_His_Comets"]),
51: dict(created="1982–1983", story="Wish You Were Here Tonight — альбом Ray Charles пізнього періоду, що поєднує soul, country-pop і дорослий contemporary pop. Югославське видання цікаве як локальний пресинг матеріалу американського артиста, а не як нова міжнародна версія альбому.", tracks="I Wish You Were Here Tonight; Let Your Love Flow; You Feel Good All Over", links=["https://en.wikipedia.org/wiki/Ray_Charles"]),
52: dict(created="1991", story="Nevermind записували в Sound City із Butch Vig, а зводив Andy Wallace. Dave Grohl приніс на альбом іншу вагу ударних, а рішення зробити «Smells Like Teen Spirit» максимально контрастним між тихим куплетом і вибуховим приспівом допомогло гранжу вийти в мейнстрим.", tracks="Smells Like Teen Spirit; Come As You Are; Something In The Way", links=["https://www.loc.gov/static/programs/national-recording-preservation-board/documents/Nevermind.pdf", "https://www.livenirvana.com/sessions/studio/may-june-1991.php"]),
53: dict(created="2021–2022", story="Patient Number 9 — пізній Ozzy, побудований як all-star-альбом: Jeff Beck, Eric Clapton, Tony Iommi, Mike McCready, Zakk Wylde й Taylor Hawkins з’являються в різних ролях. Це не просто гостьовий список, а спосіб показати різні грані його гітарної історії.", tracks="Patient Number 9; No Escape From Now; Degradation Rules", links=["https://en.wikipedia.org/wiki/Patient_Number_9"]),
54: dict(created="1954–1955", story="Оригінальний альбом записували в Capitol Studio C з аранжуваннями Nelson Riddle; це один із перших великих концептуальних LP про самотність і нічне слухання. Sinatra міг зупинити дубль після кількох нот, якщо відчував, що голос звучить не так, як має — така вимогливість чутна в інтимності платівки.", tracks="In The Wee Small Hours Of The Morning; Mood Indigo; I'll Never Be The Same", links=["https://en.wikipedia.org/wiki/In_the_Wee_Small_Hours", "https://www.soundonsound.com/techniques/classic-tracks-frank-sinatra-got-you-under-my-skin"]),
55: dict(created="1980–1981", story="Eva Olmerová — одна з найвиразніших чеських джазових співачок; тут її підтримує JOČR під керуванням Michael Kocáb. Репертуар поєднує чеські тексти з міжнародними стандартами, а аранжування балансують між soul-jazz, chanson і великим біг-бендом.", tracks="Píseň V Písni; Zahraj I Pro Mne; Žárlivost", links=["https://en.wikipedia.org/wiki/Eva_Olmerov%C3%A1"]),
56: dict(created="барокові твори XVIII ст.; оркестровка Stokowski — XX ст.", story="Leopold Stokowski відомий сміливими оркестровими транскрипціями Bach: він переносить клавішну/органну поліфонію у великий симфонічний масштаб. Česká Filharmonie на чехословацькому клубному виданні робить цей контраст особливо відчутним.", tracks="Toccata A Fuga D Moll BWV 565; Passacaglia A Fuga C Moll BWV 582", links=["https://en.wikipedia.org/wiki/Leopold_Stokowski"]),
57: dict(created="10–11 січня 1990", story="Це не студійний альбом, а віднайдений і змонтований радіозапис концертів Karel Kryl у Plzeň після повернення до Чехословаччини. Оригінальні магнітні стрічки були моно; для LP 2023 року свідомо не робили штучне стерео, зберігши документальність запису.", tracks="Morituri Te Salutant; Bratříčku, Zavírej Vrátka; Karavana Mraků", links=["https://svet.rozhlas.cz/vit-vavrina-pozadi-vzniku-alba-karel-kryl-plzen-90-9340097", "https://www.radioteka.cz/detail/crohudba-861639-karel-kryl-plzen-90"]),
}

def parse_meta(text):
    lines = [x.strip() for x in text.splitlines()]
    out = {}
    for i, line in enumerate(lines):
        if line.endswith(':') and i + 1 < len(lines):
            out[line[:-1].lower()] = lines[i + 1]
    return out

def first_tracks(raw):
    found = []
    for line in raw.splitlines():
        line = line.strip()
        m = re.match(r'^([A-D]\d+(?:\.[IVX]+)?)\s+(.*?)(?:\s+\d{1,2}:\d{2})?$', line)
        if m and len(m.group(2).strip()) > 1:
            name = re.sub(r'\s+', ' ', m.group(2).strip())
            if not name.startswith(('Written-By', 'Lead Vocals', 'Featuring', 'Piano', 'Lyrics By')) and name not in found:
                found.append(name)
    return found

def collection_fields(c):
    text = c.get('text', '')
    rating = (re.search(r'Rate this release (\d) stars', c.get('rating', '')) or [None, '—'])[1]
    added = (re.search(r'Date added\n([^\n]+)', text) or [None, '—'])[1]
    folder = (re.search(r'Folder\n([^\n]+)', text) or [None, '—'])[1]
    prices = {}
    for key in ('Minimum', 'Median', 'Maximum'):
        prices[key.lower()] = (re.search(re.escape(key) + r'\n([^\n]+)', text) or [None, '—'])[1]
    return rating, added, folder, prices

def title_parts(h):
    if ' – ' in h:
        return h.split(' – ', 1)
    return '', h

def build(items):
    lines = []
    lines += ['# Моя вінілова колекція', '', '> Зібрано з авторизованої колекції Discogs акаунта `skatt931` 7 вересня 2026 року. У каталозі 58 позицій. Метадані релізу стосуються саме вашого пресингу; “дата створення” — дата оригінального запису/альбому, якщо її вдалося відокремити від року перевидання.', '', '> Це не лише дискографічний список, а розширений путівник для прослуховування: кожна картка відділяє факти про конкретне видання від історії оригінального матеріалу, а для компіляцій і синглів пояснює їхній культурний маршрут.', '']
    lines += ['## Як читати каталог', '', '- **Оцінка Discogs** — середня оцінка спільноти; **Моя оцінка** — оцінка, збережена у вашій колекції.', '- **Рік/дата релізу** нижче — конкретний запис Discogs. Для перевидань окремо вказано, коли був створений оригінальний матеріал.', '- У кожній картці вбудовано рівно одну головну обкладинку. Посилання на галерею конкретного пресингу веде до задньої сторони, розвороту, inner sleeve, етикеток, матриці та інших фото, якщо їх завантажили користувачі Discogs.', '- Додаткові архівні посилання можуть вести до Wikimedia Commons, офіційних архівів, музеїв, студій, бібліотек, преси та відеоархівів. Мініатюри відео з Discogs навмисно не вбудовуються як “фото альбому”.', '- Для компіляцій, синглів і live-релізів дата створення означає період запису матеріалу або концерту, а не дату збірки/пізнішого видання.', '']
    lines += ['## Увесь список', '', '| № | Виконавець | Назва | Рік/країна конкретного релізу | Формат | Моя оцінка | Стан |', '|---:|---|---|---|---|---:|---|']
    for i, item in enumerate(items, 1):
        meta = parse_meta(item.get('release', {}).get('metaText', ''))
        artist, album = title_parts(item.get('release', {}).get('h', ''))
        rating, _, _, _ = collection_fields(item.get('collection', {}))
        cond = ' / '.join(item.get('collection', {}).get('conditions', [])) or '—'
        year = meta.get('released', '—')
        country = meta.get('country', '—')
        lines.append(f'| {i} | {artist} | [{album}]({item["url"]}) | {year} / {country} | {meta.get("format", "—")} | {rating} / 5 | {cond} |')
    lines += ['', '## Детальні картки релізів', '']
    for idx, item in enumerate(items):
        r = item.get('release', {})
        meta = parse_meta(r.get('metaText', ''))
        artist, album = title_parts(r.get('h', ''))
        rating, added, folder, prices = collection_fields(item.get('collection', {}))
        f = facts.get(idx, {})
        deep = research.get(idx, {})
        styles = ', '.join(r.get('styleLinks', [])) or '—'
        original = f.get('created', 'Не вдалося надійно відокремити від дати цього пресингу')
        tracks = f.get('tracks') or '; '.join(first_tracks(r.get('trackText', ''))[:4]) or 'Див. повний треклист на Discogs.'
        photo_q = quote(f'{artist} {album} {original} photo', safe='')
        artist_photo_q = quote(f'{artist} {original} portrait photo', safe='')
        studio_photo_q = quote(f'{artist} {album} recording studio session {original}', safe='')
        artwork_q = quote(f'{artist} {album} artwork inner sleeve back cover', safe='')
        period_photo = commons_period_photo(artist, original)
        lines += [f'### {idx+1}. {artist} — {album}', '', f'![Обкладинка: {artist} — {album}]({item.get("cover") or (r.get("imgs") or [{}])[0].get("src", "")})', '', f'**Discogs:** [{item["url"]}]({item["url"]})  ', f'**Оригінальний альбом / master:** [{r.get("master") or "сторінка релізу"}]({r.get("master") or item["url"]})', '']
        lines += ['#### Дані саме вашого примірника', '', f'- **Рік і дата релізу:** {meta.get("released", "—")}', f'- **Країна/ринок:** {meta.get("country", "—")}', f'- **Жанр / стиль:** {styles}', f'- **Формат:** {meta.get("format", "—")}', f'- **Лейбл і каталожний номер:** {meta.get("label", "—")}', f'- **Моя оцінка:** {rating} / 5', f'- **Стан медіа / конверта:** {item.get("collection", {}).get("conditions", ["—", "—"])[0] if item.get("collection", {}).get("conditions") else "—"} / {item.get("collection", {}).get("conditions", ["—", "—"])[1] if len(item.get("collection", {}).get("conditions", [])) > 1 else "—"}', f'- **Папка Discogs:** {folder}', f'- **Додано до колекції:** {added}', f'- **Орієнтовні ціни Discogs:** мін. {prices.get("minimum", "—")}, медіана {prices.get("median", "—")}, макс. {prices.get("maximum", "—")}', f'- **Середня оцінка Discogs:** {r.get("stats", {}).get("avg", "—")} ({r.get("stats", {}).get("ratings", "—")} оцінок)', '']
        lines += [f'#### Коли створено оригінальний матеріал: {original}', '', f.get('story', 'Для цього запису залишено нейтральну примітку: конкретний пресинг відокремлено від оригінального матеріалу; перевіряйте пов’язані джерела нижче.'), '']
        lines += ['#### Розширена історія', '', deep.get('history', 'Для цього релізу немає достатньо доступної публічної документації, щоб безпечно реконструювати детальну історію. Нижче залишено джерела для подальшої перевірки.'), '']
        lines += ['#### Як створювали запис і що було складним', '', deep.get('making', 'Публічні сесійні нотатки для цього конкретного релізу обмежені. Не підміняємо відсутні документи вигаданою студійною легендою; натомість пояснюємо контекст формату, епохи або конкретного пресингу.'), '']
        lines += [f'#### Ключові треки / на що звернути увагу', '', deep.get('tracks_detail', f'Основні треки: {tracks}.'), '', f'**Короткий орієнтир:** {tracks}', '']
        lines += ['#### Візуальний та архівний контекст', '', deep.get('visual', 'Шукайте фотографії виконавців відповідного періоду, студії, концертні афіші, рукописні тексти, партитури та матеріали оформлення.'), '', '**Фотографії саме цього видання:**', '', f'- [Галерея Discogs: обкладинка, задня сторона, розворот, етикетки, inner sleeve та інші secondary-фото]({r.get("gallery") or item["url"]})', f'- [Пошук оформлення й деталей видання у Wikimedia Commons](https://commons.wikimedia.org/w/index.php?search={artwork_q}&title=Special:MediaSearch&type=image)', '', '**Атмосфера епохи з інших джерел:**', '', f'- [Фото виконавця відповідного періоду — Wikimedia Commons](https://commons.wikimedia.org/w/index.php?search={artist_photo_q}&title=Special:MediaSearch&type=image)', f'- [Студійні, концертні та архівні фото — Wikimedia Commons](https://commons.wikimedia.org/w/index.php?search={studio_photo_q}&title=Special:MediaSearch&type=image)', f'- [Відео сесій, телеефірів і live-виступів — YouTube](https://www.youtube.com/results?search_query={studio_photo_q})', '']
        lines += ['#### Повний треклист конкретного пресингу', '', '<details><summary>Розгорнути треклист</summary>', '', '```text', r.get('trackText', 'Треклист не зчитано'), '```', '', '</details>', '']
        lines += ['#### Зображення', '', 'Вбудовано одну головну обкладинку; інші фотографії відкриваються через тематичні галереї та архівні джерела вище, щоб не дублювати обкладинку й не підміняти фото видання мініатюрами відео.', '']
        if period_photo:
            lines += [f'**Окреме архівне фото виконавця / гурту для атмосфери релізу:**', '', f'![{artist}: архівне фото]({period_photo["image"]})', '', f'- [Сторінка з описом, авторством і ліцензією цього фото: {period_photo["title"]}]({period_photo["page"]})', '']
        if f.get('links'):
            lines += ['#### Джерела та подальше читання', ''] + [f'- [{u}]({u})' for u in f['links']] + ['']
        lines += ['---', '']
    lines += ['## Примітка про джерела', '', 'Технічні поля, треклисти, конкретні країни/дати/формати, зображення та особисті оцінки взяті зі сторінок Discogs, які були доступні у вашій авторизованій сесії. Історичні нотатки звірені з офіційними сторінками артистів/лейблів, радіоархівами, музеями, Abbey Road, Library of Congress та іншими посиланнями в окремих картках. Для фото використовуйте ліцензійні умови конкретного джерела; обкладинки Discogs у файлі подані як довідкові посилання.', '']
    return '\n'.join(lines)

if __name__ == '__main__':
    raw = sys.stdin.read()
    data = json.loads(raw)
    out = Path('vinyl_collection.md')
    out.write_text(build(data), encoding='utf-8')
    print(f'Wrote {out} ({out.stat().st_size} bytes, {len(data)} releases)')
