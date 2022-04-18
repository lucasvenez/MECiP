import pandas as pd
import re

from datetime import datetime

DEGREE = "titulacao"

SUBJECTS_IN_OTHER_COURSES = "disciplinas_outros"

EXTRA_ROOM_ACTIVITIES = "atividades_extra_sala"

SUBJECTS_TAUGHT = "disciplinas_no_curso"

ADMISSION_DATE = "data_de_admissao"

WORK_REGIME = "regime_de_trabalho"

LAST_UPDATE = "ultima_atualizacao"

DEGREE = "titulacao"

NAME = "nome"

LATTES_URL = "lattes_url"


def format_personal_name(personal_name):

    if ',' not in personal_name:
        return str(personal_name).title()
    else:
        personal_name = [pn.strip().title() for pn in personal_name.split(',')]
        return personal_name[-1] + ' ' + ' '.join(personal_name[:-1])


def publication_to_str(publication):

    result = ', '.join(format_personal_name(a) for a in publication['authors']) + '. '
    result += re.sub(' +', ' ', publication['title'].title()) + '. '

    if 'journal' in publication:
        result += re.sub(' +', ' ', publication['journal'].title()) + '. '
    elif 'book' in publication:
        result += re.sub(' +', ' ', publication['book'].title()) + '. '
        result += re.sub(' +', ' ', publication['publisher'].capitalize()) + '. '
    elif 'conference' in publication:
        result += re.sub(' +', ' ', publication['conference'].title()) + '. '
        if publication['country'] is not None:
            result += re.sub(' +', ' ', publication['country'].title()) + '. '

    result += str(publication['year']) + '.'

    return result


class ProfessorIndexExtractor(object):

    ABSTRACTS_IN_CONFERENCES = 'Resumos Publicados em Conferências'
    CHAPTERS = 'Capítulos de Livros Publicados na Área'
    CHAPTERS_IN_OTHER_AREAS = 'Capítulos de Livros Publicados em Outras Áreas'
    COMPUTER_SCIENCE = 'ciência da computação'
    COURSEWARE = 'Produções Didáticas'
    EDUCATION = 'Formação Acadêmica'
    EDUCATIONAL_INSTITUTION = 'Instituição de Ensino'
    FULL_PAPERS = 'Artigos Completos Publicados em Periódicos'
    FULL_PAPERS_IN_CONFERENCES = 'Artigos Completos Publicados em Conferências'
    FULL_PAPERS_IN_OTHER_AREAS = 'Artigos Completos Publicados em Periódicos de Outras Áreas'
    HIGHER_EDUCATION_EXPERIENCE = 'Ensino Superior'
    PATENTS = 'Patentes'
    PRIMARY_EDUCATION_EXPERIENCE = 'Ensino Básico'
    PUBLICATIONS_WITHOUT_AREAS = 'Publicações sem Áreas do Conhecimento Preenchidas'
    PROFESSIONAL_EXPERIENCE = 'Experiência Profissional'
    REGISTERED_SOFTWARE = 'Software Registrado'
    SCIENTIFIC_REPORTS = 'Relatórios Científicos'
    TECHNICAL_PRODUCTIONS = 'Produções Técnicas'
    TRANSLATIONS = 'Traduções'
    UPDATE = 'Atualização'
    EMPLOYMENT_RELATIONSHIP = 'Vínculo Empregatício'

    TITLE = {1: 'Graduação',
             2: 'Especialização',
             3: 'Mestrado',
             4: 'Doutorado',
             5: 'Pós-doutorado',
             6: 'Livre-docente'}

    def __init__(self):
        self.df = {
            NAME: [],
            LATTES_URL: [],
            DEGREE: [],
            LAST_UPDATE: [],
            WORK_REGIME: [],
            ADMISSION_DATE: [],
            SUBJECTS_TAUGHT: [],
            EXTRA_ROOM_ACTIVITIES: [],
            SUBJECTS_IN_OTHER_COURSES: [],
            "xp_docencia_superior": [],
            "xp_docencia_basica": [],
            "xp_profissional": [],
            "ch_semanal": [],
            "qtd_disciplinas": [],
            "artigo_periodico_areas": [],
            "artigo_periodico_outras": [],
            "livro_capitulo_area": [],
            "livro_capitulo_outras": [],
            "anais_completo": [],
            "anais_resumo": [],
            "traducao": [],
            "propriedade_depositada": [],
            "propriedade_registrada": [],
            "relatorio_pesquisa": [],
            "producao_tecnica": [],
            "producao_didatica": []
        }

        self.inconsistencies = {}

        self.logging = {}

    def add_inconsistencies(self, k, g, v):

        if k not in self.inconsistencies:
            self.inconsistencies[k] = dict()

        if g not in self.inconsistencies[k]:
            self.inconsistencies[k][g] = [v]
        elif v not in self.inconsistencies[k][g]:
            self.inconsistencies[k][g].append(v)

    def add_log(self, k, g, v):

        if k not in self.logging:
            self.logging[k] = dict()

        if g not in self.logging[k]:
            self.logging[k][g] = [v]
        elif v not in self.logging[k][g]:
            self.logging[k][g].append(v)

    def get_higher_degree(self, row):
        formation_list = [int(e["level_code"]) for e in row["education"]
                          if str(e["level_code"]).isdigit() and 1 <= int(e["level_code"]) <= 6]

        if 1 not in [e["level_code"] for e in row["education"]]:
            self.add_inconsistencies(
                row["name"], self.EDUCATION, "A graduação não está enumerada nas formações.")

        """
        {
          "level_code": 3,
          "level": "master",
          "start": 1976,
          "end": 1977,
          "completed": true,
          "course": "Signaux Et Bruits Traitement Du Signal Et Communic",
          "institution": "Universit\u00e9 Montpellier 2 - Sciences et Techniques"
        }
        """
        for e in row["education"]:
            if str(e["level_code"]).isdigit() and 1 <= int(e["level_code"]) <= 6:
                nivel = self.TITLE[e["level_code"]]
                curso = e["course"]
                instituicao = e["institution"]
                inicio = e["start"]
                fim = e["end"]

                if e["level_code"] != 5:
                    log_message = "{} em {} pelo {} entre {} e {}".format(nivel, curso, instituicao, inicio, fim)
                else:
                    log_message = "{} pelo {} entre {} e {}".format(nivel, instituicao, inicio, fim)

                self.add_log(row["name"], self.EDUCATION, log_message)

        index = max(formation_list) - 1

        return ["G", "E", "M", "D", "D", "LD"][index]

    def get_last_update(self, row):

        months = row["months_from_last_update"]

        if months > 0:
            if months >= 2:
                self.add_inconsistencies(
                    row["name"], self.UPDATE,
                    "O CV precisa ser atualizado. Última atualização ocorreu há mais de um mês.")

            return "Há " + str(months) + (" meses " if months != 1 else " mês ") + "atrás."

        else:
            return "Atualizado este mês"

    def is_ifsp_first(self, row):
        eps = sorted(row["professional_experience"], key=lambda d: d["order"] if d["order"] is not None else 99)

        count, first_index, first_entry = 0, None, None

        for i, c in enumerate(eps):
            company = c['company_name'].lower()
            if "instituto" in company and "federal" in company and "paulo" in company and "de" in company:
                count += 1
                if first_index is None:
                    first_index = i
                    first_entry = c

        if count > 1:
            self.add_inconsistencies(
                row["name"], self.EDUCATIONAL_INSTITUTION,
                "Há duplicidade na relação de experiência profissional no IFSP.")

        if first_entry is None:
            self.add_inconsistencies(
                row["name"], self.EDUCATIONAL_INSTITUTION,
                "O IFSP não consta como primeiro item na experiência de trabalho.")

        return first_entry

    def get_work_regime(self, row):

        ep = self.is_ifsp_first(row)

        if not ep:
            return None

        if ep["weekly_workload"] is None:
            self.add_inconsistencies(
                row["name"], self.EMPLOYMENT_RELATIONSHIP,
                "A carga horária semanal não está preenchida.")

        if ep['exclusive_dedication'] and ep['weekly_workload'] == 40:
            return 'RDE'

        elif ep['weekly_workload'] is not None:
            return ep['weekly_workload'] + ' H'

    def get_admission_date(self, row):
        ep = self.is_ifsp_first(row)

        if ep:
            if len(str(ep['start'])) < 6:
                self.add_inconsistencies(
                    row['name'], self.EMPLOYMENT_RELATIONSHIP, 'A data de admissão no IFSP precisa conter ano e mês.')
            return ep['start']

        return None

    def get_taught_subjects(self, row):

        result = []

        ep = self.is_ifsp_first(row)

        if ep:
            for t in ep['teaching']:
                if t['course']:
                    course = t['course'].lower()
                    # TODO remove this hardcoded condition
                    if (
                            'análise' in course or 'analise' in course) and \
                            'sistema' in course and 'desenvolvimento' in course:
                        if str(datetime.now().year) in str(t['start']):
                            result = t['classes']
                            break

        return result

    def get_extra_activities(self, row):
        return None

    def get_classes_in_other_courses(self, row):
        ep = self.is_ifsp_first(row)

        classes = []

        if ep:
            for t in ep['teaching']:
                if t['course']:
                    course = t['course'].lower()
                    # TODO remove this hardcoded condition
                    if not (
                            ('análise' in course or 'analise' in course) and
                            'sistema' in course and 'desenvolvimento' in course):
                        if str(datetime.now().year) in str(t['start']):
                            classes += t['classes']

        if len(classes) == 0:
            return None

        return classes

    def get_experience_in_higher_education(self, row):

        months = set()

        for professional_experience in row['professional_experience']:
            for teaching in professional_experience['teaching']:
                if teaching['level'] == 'GRADUACAO':
                    start, end = teaching['start'], teaching['end']
                    if start is not None and end is not None:
                        months.update(pd.date_range('{1}-{0}-01'.format(*start.split('/')),
                                                    '{1}-{0}-01'.format(*end.split('/')),
                                                    freq='MS').strftime("%Y%m").tolist())

        if len(months) == 0:
            self.add_inconsistencies(
                row['name'], self.HIGHER_EDUCATION_EXPERIENCE,
                'Não há nenhuma informação sobre disciplinas lecionadas no ensino superior.')

        return round(len(months) / 12.0, 2)

    def get_experience_in_primary_education(self, row):

        months = set()

        for professional_experience in row['professional_experience']:
            for teaching in professional_experience['teaching']:
                if teaching['level'] == 'ENSINO-MEDIO':
                    start, end = teaching['start'], teaching['end']
                    if start is not None and end is not None:
                        months.update(pd.date_range('{1}-{0}-01'.format(*start.split('/')),
                                                    '{1}-{0}-01'.format(*end.split('/')),
                                                    freq='MS').strftime("%Y%m").tolist())

        if len(months) == 0:
            self.add_inconsistencies(
                row['name'], self.PRIMARY_EDUCATION_EXPERIENCE,
                'Não há nenhuma informação sobre disciplinas lecionadas no ensino básico.')

        return round(len(months) / 12.0, 2)

    def get_professional_experience(self, row):

        months, count = set(), 0

        for professional_experience in row['professional_experience']:

            if 'teaching' is not professional_experience:

                start, end = professional_experience['start'], professional_experience['end']

                if end is None:
                    end = datetime.now().strftime('%m/%Y')
                    count += 1

                if start is not None and end is not None:
                    if isinstance(start, int) or isinstance(end, int):
                        self.add_inconsistencies(
                            row['name'], self.PROFESSIONAL_EXPERIENCE,
                            'A experiência profissional na empresa {} tem data de término ou '
                            'fim alimentada apenas com o ano (início={}, término={})'.format(
                                professional_experience['company_name'], start, end))
                    else:
                        months.update(pd.date_range('{1}-{0}-01'.format(*start.split('/')),
                                                    '{1}-{0}-01'.format(*end.split('/')),
                                                    freq='MS').strftime("%Y%m").tolist())

        if count > 1:
            self.add_inconsistencies(
                row['name'], self.PROFESSIONAL_EXPERIENCE,
                'Há mais de uma entrada na experiência profissional sem data de término. '
                'Garanta que essa informação está correta.')

        if len(months) == 0:
            self.add_inconsistencies(
                row['name'], self.PROFESSIONAL_EXPERIENCE,
                'Não há experiência profissional fora da área de educação registrada.')

        return round(len(months) / 12.0, 2)

    def get_weekly_workload(self, row):
        ep = self.is_ifsp_first(row)
        return ep['weekly_workload'] if ep is not None else None

    def get_number_of_disciplines(self, row):
        classes = self.get_taught_subjects(row)
        return len(classes) if classes is not None else 0

    def get_full_papers(self, row):

        i = 0

        for j in row['publications']['journal_papers']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:

                if len(all_) == 0:
                    self.add_inconsistencies(
                        row['name'], self.PUBLICATIONS_WITHOUT_AREAS,
                        publication_to_str(j))

                # FIXME add full computer science tree
                if self.COMPUTER_SCIENCE in all_:
                    i += 1
                    self.add_log(row['name'], self.FULL_PAPERS, publication_to_str(j))

        return i

    def get_full_papers_in_other_areas(self, row):
        i = 0

        for j in row['publications']['journal_papers']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:

                if len(all_) == 0:
                    self.add_inconsistencies(
                        row['name'], self.PUBLICATIONS_WITHOUT_AREAS,
                        publication_to_str(j))

                # FIXME add full computer science tree
                if self.COMPUTER_SCIENCE not in all_:
                    i += 1
                    self.add_log(row['name'], self.FULL_PAPERS_IN_OTHER_AREAS, publication_to_str(j))

        return i

    def get_chapters(self, row):
        i = 0

        for j in row['publications']['books_and_chapters']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:

                if len(all_) == 0:
                    self.add_inconsistencies(
                        row['name'], self.PUBLICATIONS_WITHOUT_AREAS,
                        publication_to_str(j))

                if self.COMPUTER_SCIENCE in all_:
                    i += 1
                    self.add_log(row['name'], self.CHAPTERS, publication_to_str(j))

        return i

    def get_chapters_in_other_areas(self, row):

        i = 0

        for j in row['publications']['books_and_chapters']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:

                if len(all_) == 0:
                    self.add_inconsistencies(
                        row['name'], self.PUBLICATIONS_WITHOUT_AREAS,
                        publication_to_str(j))

                if self.COMPUTER_SCIENCE not in all_:
                    i += 1
                    self.add_log(row['name'], self.CHAPTERS_IN_OTHER_AREAS, publication_to_str(j))

        return i

    def get_full_paper_in_conference_proceedings(self, row):
        i = 0

        for j in row['publications']['conference_papers']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:

                if len(all_) == 0:
                    self.add_inconsistencies(
                        row['name'], self.PUBLICATIONS_WITHOUT_AREAS,
                        publication_to_str(j))

                if j["type"] == "full":
                    i += 1
                    self.add_log(row['name'], self.FULL_PAPERS_IN_CONFERENCES, publication_to_str(j))

        return i

    def get_abstracts_in_conference_proceedings(self, row):
        i = 0

        for j in row['publications']['conference_papers']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:

                if len(all_) == 0:
                    self.add_inconsistencies(
                        row['name'], self.PUBLICATIONS_WITHOUT_AREAS,
                        publication_to_str(j))

                if j["type"] != "full":
                    i += 1
                    self.add_log(row['name'], self.ABSTRACTS_IN_CONFERENCES, publication_to_str(j))

        return i

    def get_deposited_property(self, row):
        i = 0

        for j in row['patents']:
            if j['year'] >= datetime.now().year - 3:
                i += 1
                self.add_log(row['name'], self.PATENTS, publication_to_str(j))

        return i

    def get_registered_property(self, row):

        i = 0

        for j in row['software']:
            if j['year'] >= datetime.now().year - 3:
                if j['registered']:
                    i += 1
                    self.add_log(row['name'], self.REGISTERED_SOFTWARE, publication_to_str(j))

        return i

    def get_translations(self, row):
        i = 0

        for j in row['publications']['translations']:

            all_ = []

            for a in j["areas"]:
                for b in a:
                    all_.append(str(b).lower())

            if j['year'] >= datetime.now().year - 3:
                i += 1
                self.add_log(row['name'], self.TRANSLATIONS, publication_to_str(j))

        return i

    def get_scientific_reports(self, row):

        i = 0

        for j in row['scientific_reports']:
            if j['year'] >= datetime.now().year - 3:
                i += 1
                self.add_log(row['name'], self.SCIENTIFIC_REPORTS, publication_to_str(j))

        return i

    def get_technical_productions(self, row):
        i = 0

        for j in row['software']:
            if j['year'] >= datetime.now().year - 3:
                if not j['registered']:
                    i += 1
                    self.add_log(row['name'], self.TECHNICAL_PRODUCTIONS, publication_to_str(j))

        for j in row['event_organization']:
            if j['year'] >= datetime.now().year - 3:
                i += 1
                self.add_log(row['name'], self.TECHNICAL_PRODUCTIONS, publication_to_str(j))

        # add outras produções artisticas

        return i

    def get_didactic_production(self, row):
        i = 0

        for j in row['courseware']:
            if j['year'] >= datetime.now().year - 3:
                i += 1
                self.add_log(row['name'], self.COURSEWARE, publication_to_str(j))

        # add outras produções artisticas

        return i

    def compute_index(self, raw_data):
        for row in raw_data:
            self.df[NAME].append(row["name"])
            self.df[LATTES_URL].append(row["lattes_url"])
            self.df[DEGREE].append(self.get_higher_degree(row))
            self.df[LAST_UPDATE].append(self.get_last_update(row))
            self.df[WORK_REGIME].append(self.get_work_regime(row))
            self.df[ADMISSION_DATE].append(self.get_admission_date(row))
            self.df[SUBJECTS_TAUGHT].append(self.get_taught_subjects(row))
            self.df[EXTRA_ROOM_ACTIVITIES].append(self.get_extra_activities(row))
            self.df[SUBJECTS_IN_OTHER_COURSES].append(self.get_classes_in_other_courses(row))
            self.df["xp_docencia_superior"].append(self.get_experience_in_higher_education(row))
            self.df["xp_docencia_basica"].append(self.get_experience_in_primary_education(row))
            self.df["xp_profissional"].append(self.get_professional_experience(row))
            self.df["ch_semanal"].append(self.get_weekly_workload(row))
            self.df["qtd_disciplinas"].append(self.get_number_of_disciplines(row))
            self.df["artigo_periodico_areas"].append(self.get_full_papers(row))
            self.df["artigo_periodico_outras"].append(self.get_full_papers_in_other_areas(row))
            self.df["livro_capitulo_area"].append(self.get_chapters(row))
            self.df["livro_capitulo_outras"].append(self.get_chapters_in_other_areas(row))
            self.df["anais_completo"].append(self.get_full_paper_in_conference_proceedings(row))
            self.df["anais_resumo"].append(self.get_abstracts_in_conference_proceedings(row))
            self.df["traducao"].append(self.get_translations(row))
            self.df["propriedade_depositada"].append(self.get_deposited_property(row))
            self.df["propriedade_registrada"].append(self.get_registered_property(row))
            self.df["relatorio_pesquisa"].append(self.get_scientific_reports(row))
            self.df["producao_tecnica"].append(self.get_technical_productions(row))
            self.df["producao_didatica"].append(self.get_didactic_production(row))

        return pd.DataFrame(self.df)
