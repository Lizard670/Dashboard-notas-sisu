CREATE DATABASE NotasEnem;
USE NotasEnem;

CREATE TABLE Pessoa ( 
    idPessoa INT PRIMARY KEY AUTO_INCREMENT,  
    Nome VARCHAR(255) not null
); 

CREATE TABLE NotaEnem ( 
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

CREATE TABLE Faculdade ( 
    idFaculdade INT PRIMARY KEY AUTO_INCREMENT,  
    Sigla VARCHAR(255) not null,
    NomeFaculdade VARCHAR(255)
); 

CREATE TABLE Curso( 
    idCurso INT PRIMARY KEY AUTO_INCREMENT,  
    NomeCurso VARCHAR (255) not null,  
    Modalidade VARCHAR (255),  
    Turno VARCHAR(255),
    idFaculdade INT,  
    FOREIGN KEY(idFaculdade) REFERENCES Faculdade (idFaculdade),

    PesoLinguagens INT,  
    PesoHumanas INT,  
    PesoNaturezas INT,  
    PesoMatematica INT,  
    PesoRedacao INT
); 

CREATE TABLE Cota ( 
    idCota INT PRIMARY KEY AUTO_INCREMENT,  
    Nome VARCHAR(255) not null,  
    Descricao VARCHAR(255)  
); 

CREATE TABLE CotaCurso ( 
    idCota INT,  
    idCurso INT,  
    FOREIGN KEY(idCota) REFERENCES Cota (idCota),
    FOREIGN KEY(idCurso) REFERENCES Curso (idCurso),
    Nota FLOAT  
); 

