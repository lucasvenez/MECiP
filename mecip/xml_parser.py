# -*- coding: iso-8859-1 -*-

import io
import zipfile

from datetime import datetime, date
from lxml import html, etree


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def default_parser(component):
    if isinstance(component, (datetime, date)):
        return component.isoformat()

    return str(component)


def none_if_empty(value):

    if value == "":
        return None

    if str(value).isdigit() and not str(value).startswith("0"):
        return int(value)

    if str(value).isdecimal() and not str(value).startswith("0"):
        return float(value)

    return str(value)


def merge_month_year(month, year):
    result = None

    if month is not None:
        month = str(month)
        if len(month) == 1:
            month = "0" + month

    if month is not None and year is not None:
        result = str(month) + "/" + str(year)

    elif month is None and year is not None:
        result = int(year)

    if result == "/":
        result = None

    return result


def course_name(element):
    try:
        return none_if_empty(element.xpath("@nome-curso")[0])
    except:
        return None


def education(element):
    result = []

    xpath = "//curriculo-vitae/dados-gerais/formacao-academica-titulacao/*"

    course_level = {
        1: "undergraduate",
        2: "specialization",
        3: "master",
        4: "phd",
        5: "postdoctoral",
        6: "lecturer",
        7: "technical",
        "C": "high_school"
    }

    for e in element.xpath(xpath):

        level_code = none_if_empty(e.xpath("@nivel")[0])

        try:
            if level_code != 6:
                start = none_if_empty(e.xpath("@ano-de-inicio")[0])
            else:
                start = none_if_empty(e.xpath("@ano-de-obtencao-do-titulo")[0])
        except:
            start = None

        try:
            if level_code != 6:
                end = none_if_empty(e.xpath("@ano-de-conclusao")[0])
            else:
                end = start
        except:
            end = None

        try:
            if level_code != 6:
                completed = none_if_empty(e.xpath("@status-do-curso")[0]) == "CONCLUIDO"
            else:
                completed = True
        except:
            print(level_code, type(level_code))

        if level_code not in ['X', 'B']:
            result.append({
                "level_code": level_code,
                "level": course_level[level_code],
                "start": start,
                "end": end,
                "completed": completed,
                "course": course_name(e),
                "institution": none_if_empty(e.xpath("@nome-instituicao")[0]),
            })

    return result


def doi(element):
    try:
        return none_if_empty(element.xpath("dados-basicos-do-artigo/@doi")[0])
    except:
        return None


def extract_publication_areas(publication):
    result = []

    for a in publication.xpath("areas-do-conhecimento/*"):
        big_area = none_if_empty(a.xpath("@nome-grande-area-do-conhecimento")[0])
        area = none_if_empty(a.xpath("@nome-da-area-do-conhecimento")[0])
        sub_area = none_if_empty(a.xpath("@nome-da-sub-area-do-conhecimento")[0])
        result.append((big_area, area, sub_area))

    return result


def journal_papers(element):
    xpath = "//curriculo-vitae/producao-bibliografica/artigos-publicados/artigo-publicado"

    return [
        {
            "title": none_if_empty(journal_paper.xpath("dados-basicos-do-artigo/@titulo-do-artigo")[0]),
            "authors": [a for a in journal_paper.xpath("autores/@nome-completo-do-autor")],
            "areas": extract_publication_areas(journal_paper),
            "year": none_if_empty(journal_paper.xpath("dados-basicos-do-artigo/@ano-do-artigo")[0]),
            "journal": none_if_empty(journal_paper.xpath("detalhamento-do-artigo/@titulo-do-periodico-ou-revista")[0]),
            "start_page": none_if_empty(journal_paper.xpath("detalhamento-do-artigo/@pagina-inicial")[0]),
            "end_page": none_if_empty(journal_paper.xpath("detalhamento-do-artigo/@pagina-final")[0]),
            "volume": none_if_empty(journal_paper.xpath("detalhamento-do-artigo/@volume")[0]),
            "issn": none_if_empty(journal_paper.xpath("detalhamento-do-artigo/@issn")[0]),
            "doi": doi(journal_paper),
        } for journal_paper in element.xpath(xpath)]


def books_and_chapters(element):
    result = []

    xpath = "//curriculo-vitae/producao-bibliografica/livros-e-capitulos/capitulos-de-livros-publicados/capitulo-de-livro-publicado"

    for chapter in element.xpath(xpath):

        try:
            chapter_type = str(chapter.xpath("dados-basicos-do-capitulo/@tipo")[0]).lower()
        except:
            chapter_type = ""

        if "publicado" in chapter_type:
            result.append({
                "title": none_if_empty(chapter.xpath("dados-basicos-do-capitulo/@titulo-do-capitulo-do-livro")[0]),
                "authors": [none_if_empty(a) for a in chapter.xpath("autores/@nome-completo-do-autor")],
                "areas": extract_publication_areas(chapter),
                "year": none_if_empty(chapter.xpath("dados-basicos-do-capitulo/@ano")[0]),
                "book": none_if_empty(chapter.xpath("detalhamento-do-capitulo/@titulo-do-livro")[0]),
                "volume": none_if_empty(chapter.xpath("detalhamento-do-capitulo/@numero-de-volumes")[0]),
                "start_page": none_if_empty(chapter.xpath("detalhamento-do-capitulo/@pagina-inicial")[0]),
                "end_page": none_if_empty(chapter.xpath("detalhamento-do-capitulo/@pagina-final")[0]),
                "publisher": none_if_empty(chapter.xpath("detalhamento-do-capitulo/@nome-da-editora")[0]),
                "doi": doi(chapter),
                "type": "chapter"
            })

    xpath = "//curriculo-vitae/producao-bibliografica/livros-e-capitulos/livros-publicados-ou-organizados/livro-publicado-ou-organizado"

    for book in element.xpath(xpath):
        try:
            book_type = str(book.xpath("dados-basicos-do-capitulo/@tipo")[0]).lower()
        except:
            book_type = ""

        if "publicado" in book_type:
            result.append({
                "title": none_if_empty(book.xpath("dados-basicos-do-livro/@titulo-do-livro")[0]),
                "authors": [none_if_empty(a) for a in book.xpath("autores/@nome-completo-do-autor")],
                "areas": extract_publication_areas(book),
                "year": none_if_empty(book.xpath("dados-basicos-do-livro/@ano")[0]),
                "publisher": none_if_empty(book.xpath("detalhamento-do-livro/@nome-da-editora")[0]),
                "volume": none_if_empty(book.xpath("detalhamento-do-livro/@numero-de-volumes")[0]),
                "pages": none_if_empty(book.xpath("detalhamento-do-livro/@numero-de-paginas")[0]),
                "doi": doi(book),
                "type": "book"
            })

    return result


def country(publication):
    try:
        return none_if_empty(publication.xpath("detalhamento-do-trabalho/@pais-do-evento")[0])
    except:
        return None


def conference_papers(element):
    xpath = "//curriculo-vitae/producao-bibliografica/trabalhos-em-eventos/trabalho-em-eventos"

    result = []

    for conference_paper in element.xpath(xpath):

        try:
            conference_type = str(conference_paper.xpath("dados-basicos-do-trabalho/@natureza")[0])
        except:
            conference_type = ""

        result.append({
            "title": none_if_empty(conference_paper.xpath("dados-basicos-do-trabalho/@titulo-do-trabalho")[0]),
            "authors": [none_if_empty(a) for a in conference_paper.xpath("autores/@nome-completo-do-autor")],
            "areas": extract_publication_areas(conference_paper),
            "year": none_if_empty(conference_paper.xpath("dados-basicos-do-trabalho/@ano-do-trabalho")[0]),
            "conference": none_if_empty(conference_paper.xpath("detalhamento-do-trabalho/@nome-do-evento")[0]),
            "volume": none_if_empty(conference_paper.xpath("detalhamento-do-trabalho/@volume")[0]),
            "country": country(conference_paper),
            "type": "abstract" if "resumo" in str(conference_type) else "full"
        })

    return result


def publications(element):
    """
    [X] Artigos public. periódicos
    [X] Livros ou capítulos publicados
    [X] Trabalhos publicados em anais (completos)
    [X] Trabalhos publicados em anais (resumos)
    Traduções de livros, capítulos de livros ou artigos publicados
    """

    return {
        "journal_papers": journal_papers(element),
        "books_and_chapters": books_and_chapters(element),
        "conference_papers": conference_papers(element),
        "translations": [],  # translations(element)
    }


def professional_experiences(element):
    result = []

    xpath = '//curriculo-vitae/dados-gerais/atuacoes-profissionais/atuacao-profissional'

    for e in element.xpath(xpath):

        try:
            order = int(e.xpath("@sequencia-importancia")[0])
        except:
            order = None

        try:
            position = e.xpath("vinculos/@outro-enquadramento-funcional-informado")[0]

            start_month = none_if_empty(e.xpath("vinculos/@mes-inicio")[0])
            start_year = none_if_empty(e.xpath("vinculos/@ano-inicio")[0])

            end_month = none_if_empty(e.xpath("vinculos/@mes-fim")[0])
            end_year = none_if_empty(e.xpath("vinculos/@ano-fim")[0])

            weekly_workload = none_if_empty(e.xpath("vinculos/@carga-horaria-semanal")[0])

            exclusive_dedication = none_if_empty(e.xpath("vinculos/@flag-dedicacao-exclusiva")[0])

            teaching = [{
                "level": none_if_empty(t.xpath("@tipo-ensino")[0]),
                "start": merge_month_year(t.xpath("@mes-inicio")[0], t.xpath("@ano-inicio")[0]),
                "end": merge_month_year(t.xpath("@mes-fim")[0], t.xpath("@ano-fim")[0]),
                "course": none_if_empty(t.xpath("@nome-curso")[0]),
                "classes": [none_if_empty(c) for c in t.xpath("disciplina/text()")]
            } for t in e.xpath("atividades-de-ensino/ensino")]

            research_and_development = [
                {
                    "start": merge_month_year(r.xpath("@mes-inicio")[0], r.xpath("@ano-inicio")[0]),
                    "end": merge_month_year(r.xpath("@mes-fim")[0], r.xpath("@ano-fim")[0]),
                    "company_code": none_if_empty(r.xpath("@codigo-orgao")[0]),
                    "company_name": none_if_empty(r.xpath("@nome-orgao")[0]),
                    "research_lines": [rl for rl in r.xpath("linha-de-pesquisa/@titulo-da-linha-de-pesquisa")]
                } for r in e.xpath("atividades-de-pesquisa-e-desenvolvimento/pesquisa-e-desenvolvimento")
            ]

            result.append({
                "company_code": e.xpath("@codigo-instituicao")[0],
                "company_name": e.xpath("@nome-instituicao")[0],
                "position": none_if_empty(position),
                "weekly_workload": int(weekly_workload) if weekly_workload is not None else None,
                "start": merge_month_year(start_month, start_year),
                "end": merge_month_year(end_month, end_year),
                "exclusive_dedication": exclusive_dedication == "SIM",
                "order": order,
                "teaching": teaching,
                "research_and_development": research_and_development
            })
        except IndexError:
            pass

    return result


def name(element):
    xpath = '//curriculo-vitae/dados-gerais/@nome-completo'
    return str(element.xpath(xpath)[0])


def last_update(element):
    xpath = '//curriculo-vitae/@data-atualizacao'
    extracted_date = str(element.xpath(xpath)[0])

    last_update = datetime.strptime(extracted_date, '%d%m%Y')

    return {
        'last_update': last_update,
        'months_from_last_update': diff_month(datetime.now(), last_update)
    }


def patents(element):
    xpath = "//curriculo-vitae/producao-tecnica/patente"

    result = []

    for p in element.xpath(xpath):
        try:
            result.append({
                "title": none_if_empty(p.xpath("dados-basicos-da-patente/@titulo")[0]),
                "year": none_if_empty(p.xpath("dados-basicos-da-patente/@ano-desenvolvimento")[0]),
                "country": none_if_empty(p.xpath("dados-basicos-da-patente/@pais")[0]),
                "sponsor": none_if_empty(p.xpath("detalhamento-da-patente/@instituicao-financiadora")[0])
            })
        except:
            print(etree.tostring(p))

    return result


def softwares(element):
    xpath = "//curriculo-vitae/producao-tecnica/software"

    result = []

    for s in element.xpath(xpath):
        result.append({
            "title": s.xpath("dados-basicos-do-software/@titulo-do-software")[0],
            "year": none_if_empty(s.xpath("dados-basicos-do-software/@ano")[0]),
            "registered": len(s.xpath("detalhamento-do-software/registro-ou-patente")) > 0,
            "authors": [none_if_empty(a) for a in s.xpath("autores/@nome-completo-do-autor")],
        })

    return result


def event_organization(element):
    xpath = "//curriculo-vitae/producao-tecnica/demais-tipos-de-producao-tecnica/organizacao-de-evento"

    result = []

    for e in element.xpath(xpath):
        result.append({
            "title": none_if_empty(e.xpath("dados-basicos-da-organizacao-de-evento/@titulo")[0]),
            "year": none_if_empty(e.xpath("dados-basicos-da-organizacao-de-evento/@ano")[0]),
            "authors": [a for a in e.xpath("autores/@nome-completo-do-autor") if none_if_empty(a) is not None]
        })

    return result


def scientific_reports(element):
    xpath = "//curriculo-vitae/producao-tecnica/demais-tipos-de-producao-tecnica/relatorio-de-pesquisa"

    result = []

    for e in element.xpath(xpath):
        result.append({
            "title": none_if_empty(e.xpath("dados-basicos-do-relatorio-de-pesquisa/@titulo")[0]),
            "year": none_if_empty(e.xpath("dados-basicos-do-relatorio-de-pesquisa/@ano")[0]),
            "authors": [a for a in e.xpath("autores/@nome-completo-do-autor") if none_if_empty(a) is not None],
            "project": e.xpath("detalhamento-do-relatorio-de-pesquisa/@nome-do-projeto")[0]
        })

    return result


def courseware(element):
    xpath = "//curriculo-vitae/producao-tecnica/demais-tipos-de-producao-tecnica/desenvolvimento-de-material-didatico-ou-instrucional"

    result = []

    for e in element.xpath(xpath):
        result.append({
            'authors': [a for a in e.xpath("autores/@nome-completo-do-autor") if none_if_empty(a) is not None],
            'type': none_if_empty(e.xpath('dados-basicos-do-material-didatico-ou-instrucional/@natureza')[0]),
            'title': none_if_empty(e.xpath('dados-basicos-do-material-didatico-ou-instrucional/@titulo')[0]),
            'year': none_if_empty(e.xpath('dados-basicos-do-material-didatico-ou-instrucional/@ano')[0]),
            'link': none_if_empty(
                e.xpath('dados-basicos-do-material-didatico-ou-instrucional/@home-page-do-trabalho')[0])
        })

    return result


def lattes_url(element):

    xpath = "//curriculo-vitae/@numero-identificador"

    url = "http://lattes.cnpq.br/"

    lattes_id = none_if_empty(element.xpath(xpath)[0])

    return None if lattes_id is None else url + str(lattes_id)


def extract_information(element):
    return {
        'name': name(element),
        "lattes_url": lattes_url(element),
        **last_update(element),
        'professional_experience': professional_experiences(element),
        'publications': publications(element),
        'education': education(element),
        'patents': patents(element),
        'software': softwares(element),
        'event_organization': event_organization(element),
        'scientific_reports': scientific_reports(element),
        'courseware': courseware(element)
    }


def process_file(file_path):

    if not str(file_path).endswith('.zip'):
        with open(file_path, mode='r', encoding='iso-8859-1') as file:
            content = file.read()
            return extract_information(html.fromstring(bytes(content, encoding='iso-8859-1')))
    else:
        archive = zipfile.ZipFile(file_path, 'r')
        with archive.open('curriculo.xml', mode='r') as file:
            content = io.TextIOWrapper(file, encoding='iso-8859-1').read()
            return extract_information(html.fromstring(content.encode()))

