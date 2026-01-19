import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import logging

def main(db_config=None):
    db_config = {
        'host': 'localhost',
        'database': 'NotasEnem',
        'user': 'root',
        'password': 'toor'
    } if db_config is None else db_config
    motor_sql = sqlalchemy.create_engine(f'mysql+mysqlconnector://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:3306/{db_config["database"]}')

    logging.basicConfig(filename="ultimo.log", level=logging.DEBUG,
                        format="%(asctime)s:%(levelname)s:%(message)s")

    # Está no formato "Nome_do_arquivo:Nome_folha_do_excel"
    caminhos = {"Arquivo_notas": "Portal Sisu_Sisu 2024_Inscrições e notas de corte.xlsx:inscricao_2024",
                "Arquivo_vagas": "Portal_Sisu 2024_Vagas ofertadas.xlsx:adesao_2024",
                "Arquivo_correcoes": "correcao_cotas.xlsx:Sheet1"}

    menu = (f"\n+{'-'*43}+"
            "\n| 1 - Selecionar arquivo notas de corte     |"
            "\n| 2 - Selecionar arquivo vagas              |"
            "\n| 3 - Selecionar arquivo correção das cotas |"
            "\n| 4 - Ler instituições                      |"
            "\n| 5 - Ler campi                             |"
            "\n| 6 - Ler cursos                            |"
            "\n| 7 - Ler cotas                             |"
            "\n| 8 - Ler notas de corte                    |"
            "\n| 9 - Corrigir nomes cotas                  |"
            "\n|10 - Leitura completa                      |"
            "\n|11 - Rollback de transação                 |"
            "\n| 0 - Sair                                  |"
            f"\n+{'-'*43}+"
            "\nSelecione uma opção: ")
    opcao_int = -1

    equivalencias = ["Sair",
                     "Arquivo_notas",
                     "Arquivo_vagas",
                     "Arquivo_correcoes",
                     "Instituicao",
                     "Campus",
                     "Curso",
                     "Cota",
                     "CotaCurso",
                     "Corrigir_cotas",
                     "Leitura_completa",
                     "Rollback"]
    argumentos = {"Instituicao": {"manter": ["CO_IES", "NO_IES", "SG_IES"],
                                  "colunas": ["Codigo_IES", "Nome", "Sigla"],
                                  "duplicadas": ["Codigo_IES"]},
                  "Campus": {"manter": ["CO_IES", "NO_CAMPUS", "NO_MUNICIPIO_CAMPUS", "SG_UF_CAMPUS", "DS_REGIAO"],
                             "colunas": ["Codigo_IES", "Nome", "Cidade", "UF", "Regiao"],
                             "duplicadas": ["Codigo_IES", "Nome"]},
                  "Cota": {"manter": ["CO_IES", "TIPO_CONCORRENCIA", "DS_MOD_CONCORRENCIA"],
                           "colunas": ["Codigo_IES", "Nome", "Descricao"],
                           "duplicadas": ["Codigo_IES", "Descricao"]},
                  "Curso": {"manter": ["CO_IES", "NO_CAMPUS", "CO_IES_CURSO", "NO_CURSO", "DS_GRAU", "DS_TURNO", "PESO_LINGUAGENS", "PESO_CIENCIAS_HUMANAS", "PESO_CIENCIAS_NATUREZA", "PESO_MATEMATICA", "PESO_REDACAO"],
                            "colunas": ["CO_IES", "NomeCampus", "Codigo_IES_Curso", "Nome", "Modalidade", "Turno", "PesoLinguagens", "PesoHumanas", "PesoNaturezas", "PesoMatematica", "PesoRedacao"],
                            "duplicadas": ["Codigo_IES_Curso"]},
                  "CotaCurso": {"manter": ["CO_IES", "CO_IES_CURSO", "DS_MOD_CONCORRENCIA", "NU_NOTACORTE"],
                                "colunas": ["CO_IES", "Codigo_IES_Curso", "DS_MOD_CONCORRENCIA", "Nota"],
                                "duplicadas": []}}

    lendo_tudo = False
    while opcao_int != 0:
        try:
            if lendo_tudo:
                opcao_int += 1
            else:
                opcao_int = int(input(menu))
            opcao = equivalencias[opcao_int]
        except (IndexError, ValueError):
            print("Valor invalido")
            continue
        except KeyboardInterrupt:
            opcao_int = 0
            opcao = equivalencias[opcao_int]
        
        falhas = 0
        match opcao:
            # Seleção de arquivos
            case "Arquivo_notas" | "Arquivo_vagas" | "Arquivo_correcoes":
                print("Arquivo atual: ", caminhos[opcao])

                novo = input("Caminho do novo arquivo(Vazio para cancelar): ").split()
                if novo != "":
                    caminhos[opcao] = novo

            # Leitura de informações gerais
            case "Instituicao" |"Campus" | "Curso" | "Cota" | "CotaCurso":
                print(f"{'-'*10}=[{"Lendo " + opcao:^21}]={'-'*10}")
                # Leitura das notas de corte, está em um if diferente pois lê do arquivo de notas e não o de vagas
                if opcao in ("Cota", "CotaCurso"):
                    df = ler_generico(caminhos["Arquivo_notas"], *argumentos[opcao].values())
                else:
                    df = ler_generico(caminhos["Arquivo_vagas"], *argumentos[opcao].values())

                # Etapas necessárias pra pegar o idCampus(gerado pelo SQL)
                if opcao == "Curso":
                    with motor_sql.connect() as conexao:
                        resultado_query = conexao.execute(sqlalchemy.text('SELECT Codigo_IES, Nome, idCampus FROM Campus'))
                        dict_id_campi = {f"{linha[0]}:{linha[1]}".lower():
                                            linha[2]
                                        for linha in resultado_query}

                    sem_campus = []
                    for index, linha in df.iterrows():
                        hash_campus = f"{linha["CO_IES"]}:{linha["NomeCampus"]}".lower()

                        try:
                            df.at[index, "idCampus"] = dict_id_campi[hash_campus]
                        except KeyError:
                            sem_campus.append(index)
                            logging.warning(f"Não encontrado campus \"{hash_campus}\"")
                    

                    falhas = len(sem_campus)
                    # Remove as duas colunas que foram usadas apenas para encontraro idCampus
                    df.drop(["CO_IES", "NomeCampus"], axis=1, inplace=True)
                    # Remove os cursos que não encontrou os campus
                    df.drop(df.index[sem_campus], inplace=True)
                    df.reset_index(drop=True, inplace=True)
                # Checa se a IES está no banco antes de tentar adicionar
                # Isso é necessário já que as duas tabelas vem de planilhas diferentes
                elif opcao == "Cota":
                    institucoes = pd.read_sql("SELECT Codigo_IES FROM Instituicao", con=motor_sql).values
                    sem_IES = []
                    for index, cota in df.iterrows():
                        if cota["Codigo_IES"] not in institucoes:
                            logging.warning(f"{index} - IES [{cota["Codigo_IES"]}] não encontrada, removendo cota {cota["Nome"]} da lista")
                            sem_IES.append(index)
                    df.drop(df.index[sem_IES], inplace=True)
                    df.reset_index(drop=True, inplace=True)
                                
                # Etapas necessárias pra pegar o idCota(gerado pelo SQL)
                elif opcao == "CotaCurso":
                    df_instituicoes = pd.read_sql("SELECT Codigo_IES, Descricao, idCota FROM Cota", con=motor_sql)
                    dict_id_cotas = {f"{linha["Codigo_IES"]}:{linha["Descricao"]}".lower():
                                            linha["idCota"]
                                        for _, linha in df_instituicoes.iterrows()}

                    df["idCota"] = 0
                    sem_cota_ou_curso = []
                    cursos = pd.read_sql("SELECT Codigo_IES_Curso FROM Curso", con=motor_sql).values
                    sem_cota_ou_curso = []
                        
                    for index, linha in df.iterrows():
                        hash_cota = f"{linha["CO_IES"]}:{linha["DS_MOD_CONCORRENCIA"]}".lower()

                        

                        try:
                            df.at[index, "idCota"] = dict_id_cotas[hash_cota]
                        except KeyError:
                            sem_cota_ou_curso.append(index)
                            logging.warning(f"- Não encontrado cota \"{hash_cota}\"")
                            continue
                        else:
                            if linha["Codigo_IES_Curso"] not in cursos:
                                sem_cota_ou_curso.append(index)
                                logging.warning(f"{index} - Curso [{linha["Codigo_IES_Curso"]}] não encontrada, removendo cota {linha["idCota"]} da lista")
                                continue
                    falhas = len(sem_cota_ou_curso)
                    df.drop(df.index[sem_cota_ou_curso], inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    
                    # Remove as duas colunas que foram usadas apenas para encontraro idCota
                    df.drop(["CO_IES", "DS_MOD_CONCORRENCIA"], axis=1, inplace=True)
                
                print(f"* {len(df)} sucessos(s)")
                if falhas != 0:
                    print(f"* {falhas} falha(s)")


                # Salva no banco de dados os novos dados
                df.to_sql(name=opcao, con=motor_sql, if_exists='append', index=False)

            # Correção na sigla das cotas
            case "Corrigir_cotas":
                print(f"{'-'*10}=[{"Corrigindo cotas":^21}]={'-'*10}")
                # Cria um dicionário no formato de Nova_sigla: [Lista de descrições correspondentes]
                partes_arquivo = caminhos["Arquivo_correcoes"].split(":")
                df = pd.read_excel(partes_arquivo[0], sheet_name=partes_arquivo[1])
                cotas = {}
                for _, linha in df.iterrows():
                    if linha["Nome"] not in cotas:
                        cotas[linha["Nome"]] = []
                    cotas[linha["Nome"]].append(linha["Descricao"])

                sessao = sessionmaker(bind=motor_sql)()

                # Itera sobre todas as siglas e atualiza o banco em lotes
                mensagem_log = "Corrigindo cotas, equivalencias: \n"
                for cota, descricoes in cotas.items():
                    mensagem_log += f"    {cota}:\n"
                    for descricao in descricoes:
                        if len(descricao) > 80:
                            mensagem_log += f"        -{descricao[:77]}...\n"
                        else:
                            mensagem_log += f"        -{descricao}\n"

                    update = sqlalchemy.text("UPDATE Cota"
                                            f"    SET Nome = '{cota}'"
                                            "    WHERE Nome = 'V' AND "
                                            f"    Descricao IN ('{'\', \''.join(list(descricoes))}');")
                    sessao.execute(update)
                logging.debug(mensagem_log)
                # Salva as atualizações e fecha a sessão com o banco
                sessao.commit()
                sessao.close()

            # Ativa o modo de lendo tudo
            case "Leitura_completa":
                if not lendo_tudo:
                    print("Iniciando leitura completa")
                    lendo_tudo = True
                    opcao_int = 3
                else:
                    lendo_tudo = False
                    print("A leitura foi completada")

            # Rollback de transação
            case "Rollback":
                with motor_sql.connect() as conexao:
                    conexao.rollback()
            
            case _:
                pass

def ler_generico(arquivo, manter, colunas, duplicadas):
    partes_arquivo = arquivo.split(":")
    df = pd.read_excel(partes_arquivo[0], sheet_name=partes_arquivo[1])

    todas = list(df)
    dropar = [item for item in todas if item not in manter]
    df.drop(dropar, axis=1, inplace=True)

    df.columns = colunas
    df = df.drop_duplicates(duplicadas) if len(duplicadas) > 0 else df
    return df.reset_index(drop=True)


if __name__ == "__main__":
    main()