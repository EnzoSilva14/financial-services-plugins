# 🏛️ OSIRA Wealth Agent - POC Consolidada (Brasil)

Este repositório contém a Prova de Conceito (POC) do **OSIRA Wealth Agent**, um assistente de investimentos de elite para o mercado brasileiro, integrado com dados reais via **Open Finance (Pluggy)** e inteligência artificial 

## 🚀 O que este Agente faz?

O agente atua como um assessor de **Family Office**, sendo capaz de:

1.  **📊 Consolidação de Patrimônio:** Soma saldos de conta corrente (`BANK`), cartões de crédito (`CREDIT`) e investimentos para dar a foto real do patrimônio líquido.
2.  **⚖️ Rebalanceamento Automático:** Analisa o desvio (drift) em relação a uma alocação alvo (padrão 60% Renda Fixa / 40% Variável) e sugere aportes.
3.  **📉 Colheita de Prejuízo (Tax-Loss Harvesting):** Identifica ativos em prejuízo para fins de compensação de IR.
4.  **💸 Planejamento de Fluxo de Caixa:** Analisa o histórico de transações para projetar a capacidade de aporte mensal.
5.  **🏛️ Consultoria de Previdência:** Analisa se o cliente deve investir em PGBL ou VGBL com base no perfil.

## 📁 Estrutura do Projeto

- `app/skills/`: Lógica das 5 inteligências financeiras brasileiras.
- `app/core/pluggy_client.py`: Conexão real e segura com a API do Pluggy.
- `osira_wealth_agent.py`: Chat interativo via terminal (A POC principal).
- `.env`: Arquivo de configuração de chaves (Pluggy + OpenAI).

## 🛠️ Como Rodar

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure o seu `.env` na raiz:**
    ```env
    # Pluggy
    clientId=SUA_CHAVE_PLUGGY
    clientSecret=SEU_SECRET_PLUGGY
    itemId=ID_DO_ITEM_CONECTADO (Ex: Itaú)

    # IA
    OPENAI_API_KEY=SUA_CHAVE_OPENAI
    OPENAI_MODEL=gpt-4o
    ```

3.  **Inicie o Agente:**
    ```bash
    python osira_wealth_agent.py
    ```

## 🧠 Exemplo de Caso de Uso

**Usuário:** *"Qual é o meu patrimônio total hoje e como posso melhorar minha rentabilidade?"*

**OSIRA:** Identificará os R$ 20k parados na sua conta, os R$ 323 investidos e o uso do seu Mastercard Black. Ele sugerirá o rebalanceamento proativo para tirar o dinheiro da conta e colocá-lo para render seguindo a estratégia 60/40.

---
⚠️ *Este projeto é uma Prova de Conceito (POC)*
