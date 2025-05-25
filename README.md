# 🖧 Simulador de Rede

Um simulador visual de redes que permite posicionar dispositivos (como PCs e roteadores) em um mapa, conectar elementos e visualizar o tráfego de pacotes.

## 📁 Estrutura do Projeto

```

project/
│
├── assets/                # Imagens dos dispositivos (pc.png, roteador.png etc.)
├── backend/
│   └── network\_manager.py # Lógica de rede e persistência
├── main.py                # Arquivo principal com a UI
└── README.md              # Documentação do projeto

````

## 🛠️ Requisitos

- Python 3.8 ou superior
- Bibliotecas:
  - `tkinter` (padrão no Python)
  - `Pillow` (para redimensionar imagens)

Instale o Pillow com:

```bash
pip install Pillow
````

## ▶️ Como Executar

Clone o repositório:

```bash
git clone https://github.com/seu-usuario/simulador-rede.git
cd simulador-rede
```

Execute o aplicativo:

```bash
python main.py
```

## 💾 Salvando e Carregando Redes

As redes são salvas como arquivos JSON no mesmo diretório do projeto. Basta informar o nome desejado ao salvar ou carregar uma rede.

## 🔧 Futuras Melhorias

* Zoom e redimensionamento da área de rede
* Tooltip animado ou persistente
* Suporte a switches e servidores
* Interface em tela cheia

## 🧑‍💻 Autor

Desenvolvido por **Alyson Vinicius Galdino de Souza**
📧 Contato: \[[alysonvinicius.dev@gmail.com](mailto:alysonvinicius.dev@gmail.com)]
🔗 GitHub: [github.com/alysonvinicius](https://github.com/alysonvinicius)

```

```
