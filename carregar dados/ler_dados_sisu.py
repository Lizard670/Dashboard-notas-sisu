import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker

def main(db_config=None):
    db_config = {
        'host': 'localhost',
        'database': 'NotasEnem',
        'user': 'root',
        'password': 'toor'
    } if db_config is None else db_config
    motor_sql = sqlalchemy.create_engine(f'mysql+mysqlconnector://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:3306/{db_config["database"]}')

    arquivo = "Portal Sisu_Sisu 2025_Inscrições e notas de corte.xlsx:inscricao_2025_1"
    arquivo_pesos = "ResultadoDia4.xlsx:Sheet1"

    menu = (f"\n+{'-='*16}-+"
            "\n|1 - Selecionar arquivo principal |"
            "\n|2 - Selecionar arquivo pesos     |"
            "\n|3 - Ler instituições             |"
            "\n|4 - Ler campi                    |"
            "\n|5 - Ler cursos                   |"
            "\n|6 - Ler cotas                    |"
            "\n|7 - Ler notas de corte           |"
            "\n|8 - Corrigir nomes cotas         |"
            "\n|0 - Sair                         |"
            f"\n+{'-='*16}-+"
            "\nSelecione uma opção: ")
    opcao = -1
    
    equivalencias = {3: "instituicao",
                     4: "campus", 
                     5: "curso", 
                     6: "cota", 
                     7: "cotacurso"}
    argumentos = {"instituicao": {"manter": ["CO_IES", "NO_IES", "SG_IES"],
                                  "colunas": ["Codigo_IES", "Nome", "Sigla"],
                                  "duplicadas": ["Codigo_IES"]},
                  "campus": {"manter": ["CO_IES", "NO_CAMPUS", "NO_MUNICIPIO_CAMPUS", "SG_UF_CAMPUS", "DS_REGIAO_CAMPUS"],
                             "colunas": ["Codigo_IES", "Nome", "Cidade", "UF", "Regiao"],
                             "duplicadas": ["Codigo_IES", "Nome"]},
                  "cota": {"manter": ["CO_IES", "TIPO_CONCORRENCIA", "DS_MOD_CONCORRENCIA"],
                           "colunas": ["Codigo_IES", "Nome", "Descricao"],
                           "duplicadas": ["Codigo_IES", "Descricao"]},
                  "curso": {"manter": ["CO_IES", "NO_CAMPUS", "CO_IES_CURSO", "NO_CURSO", "DS_GRAU", "DS_TURNO"],
                            "colunas": ["CO_IES", "NomeCampus", "Codigo_IES_Curso", "Nome", "Modalidade", "Turno"],
                            "duplicadas": ["Codigo_IES_Curso"]},
                  "cotacurso": {"manter": ["CO_IES", "CO_IES_CURSO", "DS_MOD_CONCORRENCIA", "NU_NOTACORTE"],
                                "colunas": ["CO_IES", "Codigo_IES_Curso", "DS_MOD_CONCORRENCIA", "Nota"],
                                "duplicadas": []}}
    
    while opcao != 0:
        try:
            opcao = int(input(menu))
            if not 0 <= opcao <= 8:
                raise ValueError
        except ValueError:
            print("Valor invalido")
            continue
        except KeyboardInterrupt:
            opcao = 0

        if opcao == 1:
            print("Arquivo atual: ", arquivo)
            novo = input("Caminho do novo arquivo(Vazio para cancelar): ").split()
            if novo != "":
                arquivo = novo
        if opcao == 2:
            print("Arquivo atual: ", arquivo_pesos)
            novo = input("Caminho do novo arquivo(Vazio para cancelar): ").split()
            if novo != "":
                arquivo_pesos = novo

        if opcao == 8:
            df = pd.read_excel("correcao_cotas.xlsx", sheet_name="Sheet1")
            cotas = {}
            for _, linha in df.iterrows():
                if linha["Nome"] not in cotas:
                    cotas[linha["Nome"]] = []
                cotas[linha["Nome"]].append(linha["Descricao"])
            
            sessao = sessionmaker(bind=motor_sql)()

            for cota, descricoes in cotas.items():
                print(f"{cota}:")
                for descricao in descricoes:
                    if len(descricao) > 80:
                        print(f"    -{descricao[:80]}")
                    else:
                        print(f"    -{descricao}")
                tabela_cota = sqlalchemy.table("cota")
                update = sqlalchemy.text("UPDATE cota"
                                        f"    SET nome = '{cota}'"
                                         "    WHERE nome = 'V' AND "
                                        f"    descricao IN ('{'\', \''.join(list(descricoes))}');")
                sessao.execute(update) 
            sessao.commit()
            sessao.close()

        elif 2 < opcao <= 7:
            tabela = equivalencias[opcao]
            df = ler_generico(arquivo, *argumentos[tabela].values())

            # Etapas necessárias pra pegar o idCampus(gerado pelo SQL) e o Peso das notas (Não presente na planilha principal)
            if tabela == "curso":
                with motor_sql.connect() as conexao:
                    resultado_query = conexao.execute(sqlalchemy.text('SELECT Codigo_IES, Nome, idCampus  FROM Campus'))
                    hash_id_campi = {f"{linha[0]}:{linha[1]}".lower(): 
                                        linha[2] 
                                     for linha in resultado_query}
                df["idCampus"] = 0
                df["PesoLinguagens"] = 1
                df["PesoHumanas"] = 1
                df["PesoNaturezas"] = 1
                df["PesoMatematica"] = 1
                df["PesoRedacao"] = 1
                    

                df_pesos = ler_generico(arquivo_pesos, 
                                        manter = ["CodigoIES", "Campus", "Nome_Curso", "Peso_Nota_CN", "Peso_Nota_MT", "Peso_Nota_L", "Peso_Nota_CH", "Peso_Nota_REDACAO"],
                                        colunas = ["CO_IES", "NO_CAMPUS", "Nome", "PesoNaturezas", "PesoMatematica", "PesoLinguagens", "PesoHumanas","PesoRedacao"],
                                        duplicadas= ["CO_IES", "NO_CAMPUS", "Nome"],
                                        todas = ["CodigoSISU", "CodigoIES", "Universidade", "Nome_Estado", "Nome_Municipio_Campus", "Campus", "Nome_Curso", "Grau", "Turno", "Cota", "Quant_Vagas_Cota", "Minimo_Nota_CN", "Peso_Nota_CN", "Minimo_Nota_MT", "Peso_Nota_MT", "Minimo_Nota_L", "Peso_Nota_L", "Minimo_Nota_CH", "Peso_Nota_CH", "Minimo_Nota_REDACAO", "Peso_Nota_REDACAO", "Media_Minima", "Bonus_Percentual", "Nota_Corte_1_Dia", "Diferenca_Corte_1_Para_2_Dia", "Nota_Corte_2_Dia", "Diferenca_Corte_2_Para_3_Dia", "Nota_Corte_3_Dia", "Diferenca_Corte_3_Para_4_Dia", "Nota_Corte_4_Dia"])
                hash_pesos = {f"{linha["CO_IES"]}:{linha["NO_CAMPUS"]}:{linha["Nome"]}".lower(): 
                                [linha["PesoLinguagens"], linha["PesoHumanas"], linha["PesoNaturezas"], linha["PesoMatematica"], linha["PesoRedacao"]]
                              for _, linha in df_pesos.iterrows()}

                sucessos = 0
                falhas_id = 0
                falhas_pesos = 0
                for index, linha in df.iterrows():
                    hash_id = f"{linha["CO_IES"]}:{linha["NomeCampus"]}".lower()
                    hash_peso = f"{linha["CO_IES"]}:{linha["NomeCampus"]}:{linha["Nome"]}".lower()

                    try:
                        df.at[index, "idCampus"] = hash_id_campi[hash_id]
                    except KeyError:
                        print(f"- Não encontrado curso \"{hash_id}\"")
                        falhas_id += 1
                        continue

                    try:
                        df.at[index, "PesoLinguagens"] = hash_pesos[hash_peso][0]
                        df.at[index, "PesoHumanas"] = hash_pesos[hash_peso][1]
                        df.at[index, "PesoNaturezas"] = hash_pesos[hash_peso][2] 
                        df.at[index, "PesoMatematica"] = hash_pesos[hash_peso][3]
                        df.at[index, "PesoRedacao"] = hash_pesos[hash_peso][4]
                    except KeyError:
                        print(f"- Não encontrado curso \"{hash_peso}\"")
                        falhas_pesos += 1
                        continue

                    sucessos += 1

                df.drop(["CO_IES", "NomeCampus"], axis=1, inplace=True)
                print(f"Sucessos: {sucessos}")
                print(f"Falhas id: {falhas_id}")
                print(f"Falhas pesos: {falhas_pesos}")
            # Etapas necessárias pra pegar o idCota(gerado pelo SQL)
            elif tabela == "cotacurso":
                with motor_sql.connect() as conexao:
                    resultado_query = conexao.execute(sqlalchemy.text('SELECT Codigo_IES, Descricao, idCota  FROM Cota'))
                    hash_id_cota = {f"{linha[0]}:{linha[1]}".lower(): 
                                        linha[2] 
                                     for linha in resultado_query}
                df["idCota"] = 0
                for index, linha in df.iterrows():
                    hash_id = f"{linha["CO_IES"]}:{linha["DS_MOD_CONCORRENCIA"]}".lower()

                    try:
                        df.at[index, "idCota"] = hash_id_cota[hash_id]
                    except KeyError:
                        print(f"- Não encontrado cota \"{hash_id}\"")
                df.drop(["CO_IES", "DS_MOD_CONCORRENCIA"], axis=1, inplace=True)

            df.to_sql(name=tabela, con=motor_sql, if_exists='append', index=False)



def ler_generico(arquivo, manter, colunas, duplicadas, todas=None):
    partes_arquivo = arquivo.split(":")
    if todas is None:
        todas = ["EDICAO", "CO_IES", "NO_IES", "SG_IES", "DS_ORGANIZACAO_ACADEMICA", "DS_CATEGORIA_ADM", "NO_CAMPUS", "NO_MUNICIPIO_CAMPUS", "SG_UF_CAMPUS", "DS_REGIAO_CAMPUS", "CO_IES_CURSO", "NO_CURSO", "DS_GRAU", "DS_TURNO", "TP_MOD_CONCORRENCIA", "TIPO_CONCORRENCIA", "DS_MOD_CONCORRENCIA", "NU_PERCENTUAL_BONUS", "QT_VAGAS_OFERTADAS", "NU_NOTACORTE", "QT_INSCRICAO"]
    dropar = [item for item in todas if item not in manter]
    
    df = pd.read_excel(partes_arquivo[0], sheet_name=partes_arquivo[1])
    df.drop(dropar, axis=1, inplace=True)

    df.columns = colunas
    if len(duplicadas) > 0:
        return df.drop_duplicates(duplicadas)
    else:
        return df
    

if __name__ == "__main__":
    main()