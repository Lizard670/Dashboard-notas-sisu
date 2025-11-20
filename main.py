from dash import Dash, html, dcc, Input, Output  
import dash_ag_grid as dag                       
import dash_bootstrap_components as dbc          
import pandas as pd                              
import mysql.connector
import numpy as np

def main():
    db_config = {
        'host': 'localhost',
        'database': 'NotasEnem',
        'user': 'root',
        'password': 'toor'
    }
    db_config = db_config
    conexao = mysql.connector.connect(**db_config)

    #
    df_opcoes_notas = pd.read_sql('SELECT CONCAT(Pessoa.nome, " ", NotaEnem.ano) as Enem, idProva FROM NotaEnem JOIN Pessoa ON NotaEnem.idPessoa = Pessoa.idPessoa', con=conexao)
    opcoes_notas = {linha["idProva"]: linha["Enem"] for index, linha in df_opcoes_notas.iterrows()}
    print(opcoes_notas)
    df_opcoes_cotas = pd.read_sql('SELECT Nome, idCota FROM Cota', con=conexao)
    opcoes_cotas = {linha["idCota"]: linha["Nome"] for index, linha in df_opcoes_cotas.iterrows()}

    df_opcoes_faculdades = pd.read_sql('SELECT Sigla, idFaculdade FROM Faculdade', con=conexao)
    opcoes_faculdades = {linha["idFaculdade"] : linha["Sigla"] for index, linha in df_opcoes_faculdades.iterrows()}

    # Cria o app do frontend
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = gerar_layout(opcoes_notas, opcoes_cotas, opcoes_faculdades)

    @app.callback(
        Output('tabela', 'rowData'),
        Input('nota', 'value'),
        Input('cota', 'value'),
        [Input('faculdades_filtro', 'value')],
    )

    def atualizar_pagina(id_prova, id_cota, faculdades):
        linhas_tabela = []
        faculdades = [] if faculdades is None else faculdades
        if id_cota is None or id_prova is None:
            return linhas_tabela

        # Pega as notas de corte de determinada cota
        notas_de_corte = pd.read_sql('SELECT' 
                                    '    Faculdade.Sigla as Faculdade, '
                                    '    CONCAT(Curso.NomeCurso, " ", Curso.Modalidade, " ", Curso.Turno) as Curso, '
                                    '    Nota, '
                                    '    Curso.PesoLinguagens, Curso.PesoHumanas, Curso.PesoNaturezas, Curso.PesoMatematica, Curso.PesoRedacao '
                                    'FROM CotaCurso '
                                    '    INNER JOIN Curso on CotaCurso.idCurso = Curso.idCurso '
                                    '    INNER JOIN Faculdade on Curso.idFaculdade = Faculdade.idFaculdade '
                                    f'WHERE idCota = {id_cota};', con=conexao)
        
        # Pega as notas da prova
        nota_enem = pd.read_sql(f'SELECT * FROM NotaEnem WHERE idProva = {id_prova};', con=conexao).to_dict('records')[0]
        lista_notas = [nota_enem["Linguagens"], nota_enem["Humanas"], nota_enem["Naturezas"], nota_enem["Matematica"], nota_enem["Redacao"]]
        
        # Cria cada linha da tabela, tendo as colunas: "Faculdade", "Curso", "Média com peso", "Nota de corte", "Passa?"
        for index, linha in notas_de_corte.iterrows():
            lista_pesos = [linha["PesoLinguagens"], linha["PesoHumanas"], linha["PesoNaturezas"], linha["PesoMatematica"], linha["PesoRedacao"]]
            media = np.average(lista_notas, weights=lista_pesos)

            passou = "Sim" if media >= linha["Nota"] else "Não"
            linhas_tabela.append([linha["Faculdade"], linha["Curso"], round(media, 2), linha["Nota"], passou])
        return pd.DataFrame(linhas_tabela, columns=["Faculdade", "Curso", "Média com peso", "Nota de corte", "Passa?"]).to_dict('records')
    
    
    app.run(debug=False, port=8002)


def gerar_layout(opcoes_notas, opcoes_cotas, opcoes_faculdades):
    colunas_tabela = [{"field": i} for i in ["Faculdade", "Curso", "Média com peso", "Nota de corte", "Passa?"]]
    container = dbc.Container([
        # Título
        html.H1("Quais cursos eu passo?", style={'textAlign':'center'}),

        # Dropboxes para seleção do gráfico
        dbc.Row([
            dbc.Col([
                html.H2("Nota", style={'textAlign':'center'}),
                dcc.Dropdown(
                    id='nota',
                    options=opcoes_notas)
            ], width=4),

            dbc.Col([
                html.H2("Cota", style={'textAlign':'center'}),
                dcc.RadioItems(
                    id='cota',
                    options=opcoes_cotas)
            ], width=1),

            dbc.Col([
                html.H2("Faculdades", style={'textAlign':'center'}),
                dcc.Checklist(
                    id='faculdades_filtro',
                    options=opcoes_faculdades)
            ], width=1)
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