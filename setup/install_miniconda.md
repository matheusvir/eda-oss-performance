# 🐍 Como Instalar o Miniconda

> Vamos usar o **Miniconda** para isolar ambientes de desenvolvimento e evitar conflitos de dependências entre projetos — algo que com certeza vai acontecer se você reunir um balai de dependências no seu environment global.

---

## 📑 Sumário

- [Baixar o Miniconda](#-baixar-o-miniconda)
  - [Windows](#-windows)
  - [Linux](#-linux)
- [Criar um ambiente virtual](#-criar-um-ambiente-virtual)
- [Ativar o ambiente virtual](#-ativar-o-ambiente-virtual)
- [Desativar o ambiente virtual](#-desativar-o-ambiente-virtual)
- [Dicas de uso](#-dicas-de-uso)

---

## 📥 Baixar o Miniconda

### 🪟 Windows

> **Se você usa WSL, siga o tutorial para Linux.**

👉 [Veja este vídeo](https://youtu.be/AgnAs0nPEVg)

### 🐧 Linux

Execute os seguintes comandos no seu terminal e siga os passos de instalação — você terá apenas que dar <kbd>Enter</kbd> algumas vezes e aceitar os termos de uso, nada demais.

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

> **✅ Verificando a instalação:** para testar se o Miniconda foi instalado, use:
>
> ```bash
> conda --version
> ```
>
> Se o output for algo como `conda 25.11.1`, parabéns! O Miniconda foi instalado com sucesso. 🎉
>
> Caso contrário, reinicie o terminal e tente de novo — provavelmente vai funcionar.

---

## 📦 Criar um ambiente virtual

Agora que você tem o Miniconda instalado, pode criar **ambientes virtuais** para isolar os projetos.

> 💡 **O que é um ambiente virtual?**
> Imagine que ele é como um container onde você instala as dependências do seu projeto sem afetar o resto do sistema. Por enquanto, isso é suficiente.

### Como criar:

```bash
conda create -n nome_do_ambiente python=versão_do_python
```

É interessante usar a mesma versão do Python que o projeto vai utilizar, para evitar problemas de compatibilidade. No entanto, todos os projetos que vamos trabalhar funcionam com a versão mais recente do Python, então você pode omitir a versão:

```bash
conda create -n nome_do_ambiente
```

---

## ▶️ Ativar o ambiente virtual

Após criar o ambiente virtual, você precisa ativá-lo para poder usá-lo:

```bash
conda activate nome_do_ambiente
```

Pronto! Agora você está dentro do ambiente virtual e pode instalar as dependências do seu projeto sem afetar o resto do sistema.

> ⚠️ **Usando o VSCode?**
> É provável que ele não reconheça automaticamente o ambiente virtual que você criou. Para resolver:
>
> 1. Pressione <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>
> 2. Digite **Python: Select Interpreter**
> 3. Selecione o ambiente virtual que você criou na lista
>
> Caso ele não apareça, reinicie o VSCode e tente de novo.

---

## ⏹️ Desativar o ambiente virtual

Quando terminar de trabalhar no seu projeto, é importante desativar o ambiente virtual para evitar problemas de dependências no futuro:

```bash
conda deactivate
```

---

## 💡 Dicas de uso

| Ação | Comando |
|---|---|
| Buscar pacote no Conda | `conda search nome_do_pacote` |
| Instalar pacote pelo Conda | `conda install nome_do_pacote` |
| Instalar pip no ambiente | `conda install pip` |
| Instalar pacote pelo pip | `pip install nome_do_pacote` |

> **📌 Regra de ouro:** sempre que for instalar um pacote, verifique primeiro se ele está disponível pelo Conda:
>
> ```bash
> conda search nome_do_pacote
> ```
>
> Se não estiver disponível, instale o **pip** dentro do ambiente virtual e use-o como alternativa:
>
> ```bash
> conda install pip
> pip install nome_do_pacote
> ```
