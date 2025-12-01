from dash import Dash, html, dcc, Input, Output
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import sqlalchemy
import numpy as np

def main():
    db_config = {
        'host': 'localhost',
        'database': 'NotasEnem',
        'user': 'root',
        'password': 'toor'
    }
    db_config = db_config
    motor_sql = sqlalchemy.create_engine(f'mysql+mysqlconnector://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:3306/{db_config["database"]}')

    #
    df_opcoes_notas = pd.read_sql('SELECT CONCAT(Pessoa.nome, " ", NotaEnem.ano) as Enem, idProva FROM NotaEnem JOIN Pessoa ON NotaEnem.idPessoa = Pessoa.idPessoa', con=motor_sql)
    opcoes_notas = {linha["idProva"]: linha["Enem"] for index, linha in df_opcoes_notas.iterrows()}

    #
    df_opcoes_turno = pd.read_sql('SELECT Turno FROM Curso GROUP BY Turno;', con=motor_sql)
    opcoes_turno = df_opcoes_turno['Turno'].tolist()

    # Cria o app do frontend
    app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])
    app.layout = gerar_layout(opcoes_notas, opcoes_turno)

    @app.callback(
        Output('tabela', 'rowData'),
        Output("estados", "options"),
        Output("cidades", "options"),
        Output("instituicoes", "options"),
        Output("cotas", "options"),

        Input('nota', 'value'),
        [Input('estados', 'value')],
        [Input('cidades', 'value')],
        [Input('instituicoes', 'value')],
        [Input('cotas', 'value')],
        [Input('turno', 'value')],
    )

    def atualizar_pagina(id_nota, estados, cidades, instituicoes, cotas, turno):
        linhas_tabela = []
        estados = [] if estados is None else estados
        cidades = [] if cidades is None else cidades
        instituicoes = [] if instituicoes is None else instituicoes
        cotas = [] if cotas is None else cotas
        turno = [] if turno is None else turno

        select_estados = "SELECT UF FROM Campus GROUP BY UF ORDER BY UF "
        opcoes_estados = pd.read_sql(select_estados, con=motor_sql)["UF"].tolist()

        select_cidades = "SELECT Cidade FROM Campus "
        select_cidades += f"    WHERE UF IN ('{"', '".join(estados)}') " if len(estados) > 0 else ""
        select_cidades += "GROUP BY Cidade ORDER BY Cidade"
        opcoes_cidades = pd.read_sql(select_cidades, con=motor_sql)["Cidade"].tolist()

        select_cotas = ("SELECT idCota,"
                       "    CONCAT(Cota.nome, ' ', Instituicao.sigla) as Nome, "
                       "    Descricao "
                       "    FROM Cota "
                       "    JOIN Instituicao on Cota.Codigo_IES = Instituicao.Codigo_IES "
                      f"    WHERE Cota.Codigo_IES IN ('{"', '".join(instituicoes)}')"
                       "     ORDER BY Instituicao.Sigla ")
        opcoes_cotas = [{"value": str(linha["idCota"]), "label": linha["Nome"], "title": linha["Descricao"]}
                        for _, linha in pd.read_sql(select_cotas, con=motor_sql).iterrows()]


        select_instituicoes = ("SELECT Instituicao.Codigo_IES, "
                              "    Instituicao.Nome, "
                              "    Sigla "
                              "    FROM Instituicao "
                              "    JOIN Campus on Campus.Codigo_IES = Instituicao.Codigo_IES")
        if sum(len(lista) > 0 for lista in [estados, cidades]) > 0:
            select_instituicoes += "    WHERE "
            if len(estados) > 0:
                select_instituicoes += f"        UF IN ('{"', '".join(estados)}') "

            if (sum(len(lista) > 0 for lista in [estados, cidades]) > 1):
                select_instituicoes += "AND "

            if len(cidades) > 0:
                select_instituicoes += f"        Cidade IN ('{"', '".join(cidades)}') "
        select_instituicoes += "    GROUP BY Instituicao.Codigo_IES ORDER BY Sigla"
        opcoes_instituicoes = [{"value": str(linha["Codigo_IES"]), "label": linha["Sigla"], "title": linha["Nome"]}
                                for _, linha in pd.read_sql(select_instituicoes, con=motor_sql).iterrows()]

        # Pega as notas de corte de determinada cota
        comando_query = ('SELECT'
                         '    Instituicao.Sigla as Instituicao, '
                         '    Curso.Nome as Curso, '
                         '    Curso.Modalidade as Modalidade,'
                         '    Curso.Turno as Turno,'
                         '    Cota.nome as Cota, '
                         '    Nota, '
                         '    Curso.PesoLinguagens, Curso.PesoHumanas, Curso.PesoNaturezas, Curso.PesoMatematica, Curso.PesoRedacao '
                         '    FROM CotaCurso '
                         '        INNER JOIN Curso on CotaCurso.Codigo_IES_Curso = Curso.Codigo_IES_Curso'
                         '        INNER JOIN Cota on CotaCurso.idCota = Cota.idCota'
                         '        INNER JOIN Instituicao on Cota.Codigo_IES = Instituicao.Codigo_IES '
                        f'    WHERE CotaCurso.idCota IN ("{'", "'.join(cotas)}") ')
        comando_query += f'AND Curso.Turno in ("{'", "'.join(turno)}") ' if len(turno) > 0 else ""
        notas_de_corte = pd.read_sql(comando_query, con=motor_sql)
        # Pega as notas da prova
        if id_nota is not None:
            nota_enem = pd.read_sql(f'SELECT * FROM NotaEnem WHERE idProva = {id_nota};', con=motor_sql).to_dict('records')[0]
            lista_notas = [nota_enem["Linguagens"], nota_enem["Humanas"], nota_enem["Naturezas"], nota_enem["Matematica"], nota_enem["Redacao"]]
        else:
            lista_notas = [0, 0, 0, 0, 0]

        # Cria cada linha da tabela, tendo as colunas: "Faculdade", "Curso", "Modalidade", "Turno", "Cota", "Média com peso", "Nota de corte", "Passa?"
        for _, linha in notas_de_corte.iterrows():
            lista_pesos = [linha["PesoLinguagens"], linha["PesoHumanas"], linha["PesoNaturezas"], linha["PesoMatematica"], linha["PesoRedacao"]]
            media = np.average(lista_notas, weights=lista_pesos)

            passou = "Sim" if media >= linha["Nota"] else "Não"
            linhas_tabela.append([linha["Instituicao"], linha["Curso"], linha["Modalidade"], linha["Turno"], linha["Cota"], round(media, 2), linha["Nota"], passou])

        return (pd.DataFrame(linhas_tabela, columns=["Instituição", "Curso", "Modalidade", "Turno", "Cota", "Média com peso", "Nota de corte", "Passa?"]).to_dict('records'),
                opcoes_estados,
                opcoes_cidades,
                opcoes_instituicoes,
                opcoes_cotas)


    app.run(debug=False, port=8002)


def gerar_layout(opcoes_notas, opcoes_turno):
    colunas_tabela = [{"field": i} for i in ["Instituição", "Curso", "Modalidade", "Turno", "Cota", "Média com peso", "Nota de corte", "Passa?"]]
    container = dbc.Container([
        # Título
        html.H1("Quais cursos eu passo?", style={'textAlign':'center'}),

        dbc.Row([
            dbc.Col([
                html.H2("Nota", style={'textAlign':'center'}),
                dcc.Dropdown(
                    id='nota',
                    options=opcoes_notas)
            ], width=4),

            dbc.Col([
                html.H2("Cota", style={'textAlign':'center'}),
                dcc.Dropdown(id='cotas', multi=True, closeOnSelect=False)
            ], width=2),

            dbc.Col([
                html.H2("Turno", style={'textAlign':'center'}),
                dcc.Dropdown(id='turno', options=opcoes_turno, multi=True, closeOnSelect=False)
            ], width=2)
        ]),

        dbc.Row([
            dbc.Col([
                html.H2("Estado", style={'textAlign':'center'}),
                dcc.Dropdown(id='estados', multi=True, closeOnSelect=False)
            ], width=2),

            dbc.Col([
                html.H2("Cidade", style={'textAlign':'center'}),
                dcc.Dropdown(id='cidades', multi=True, closeOnSelect=False)
            ], width=4),

            dbc.Col([
                html.H2("Instituições", style={'textAlign':'center'}),
                dcc.Dropdown(id='instituicoes', multi=True, closeOnSelect=False)
            ], width=2)
        ]),

        dbc.Row([
            dbc.Col([
                dag.AgGrid(
                    columnDefs=colunas_tabela,
                    id='tabela'
                )
            ], width=12)
        ]),
    ])

    return container


if __name__ == "__main__":
    main()