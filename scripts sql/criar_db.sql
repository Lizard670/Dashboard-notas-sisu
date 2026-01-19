CREATE DATABASE IF NOT EXISTS NotasEnem;
USE NotasEnem;

CREATE TABLE IF NOT EXISTS Pessoa ( 
    idPessoa INT PRIMARY KEY AUTO_INCREMENT,  
    Nome VARCHAR(255) not null
); 

CREATE TABLE IF NOT EXISTS NotaEnem ( 
    idProva INT PRIMARY KEY AUTO_INCREMENT,  
    Ano INT,
    idPessoa INT,
    FOREIGN KEY(idPessoa) REFERENCES Pessoa (idPessoa),

    Linguagens FLOAT,  
    Humanas FLOAT,  
    Naturezas FLOAT,  
    Matematica FLOAT,  
    Redacao INT
); 

CREATE TABLE IF NOT EXISTS Instituicao ( 
    Codigo_IES INT PRIMARY KEY,  
    Sigla VARCHAR(255) not null,
    Nome VARCHAR(255)
); 

CREATE TABLE IF NOT EXISTS Campus (
	idCampus INT PRIMARY KEY AUTO_INCREMENT,
    Codigo_IES INT, 
    FOREIGN KEY(Codigo_IES) REFERENCES Instituicao (Codigo_IES),
    
    Nome VARCHAR(255),
    Cidade VARCHAR(255),
    UF VARCHAR(255),
    Regiao VARCHAR(255)
); 

CREATE TABLE IF NOT EXISTS Curso( 
    Codigo_IES_Curso INT PRIMARY KEY,  
    idCampus INT,  
    FOREIGN KEY(idCampus) REFERENCES Campus (idCampus),
    Nome VARCHAR (255) not null,  
    Modalidade VARCHAR (255),  
    Turno VARCHAR(255),

    PesoLinguagens INT,  
    PesoHumanas INT,  
    PesoNaturezas INT,  
    PesoMatematica INT,  
    PesoRedacao INT
); 

CREATE TABLE IF NOT EXISTS Cota ( 
    idCota INT PRIMARY KEY AUTO_INCREMENT,  
    Codigo_IES INT, 
    FOREIGN KEY(Codigo_IES) REFERENCES Instituicao (Codigo_IES),
    
    Nome VARCHAR(256) not null,  
    Descricao VARCHAR(2048)  
); 

CREATE TABLE IF NOT EXISTS CotaCurso ( 
    idCota INT,  
    Codigo_IES_Curso INT,  
    FOREIGN KEY(idCota) REFERENCES Cota (idCota),
    FOREIGN KEY(Codigo_IES_Curso) REFERENCES Curso (Codigo_IES_Curso),
    Nota FLOAT  
); 

