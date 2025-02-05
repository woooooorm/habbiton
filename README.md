# Habbiton

Habbiton is a project aimed at helping users build and maintain good habits through a convinient Telegram bot.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/woooooorm/habbiton.git
    ```
2. Navigate to the project directory:
    ```sh
    cd habbiton
    ```
3. Create a bot in Telegram via @BotFather, copy the token
4. Create an .env file and populate following consts:
   ```sh
    POSTGRES_USER= <username for db>
    POSTGRES_PASSWORD= <password for db>
    POSTGRES_DB= <db name>
    TG_BOT_TOKEN= <Telegram bot token>
    ```
5. Start the containers:
    ```sh
    docker compose up -d
    ```
6. Once containers are up, you can run the test with the following comand:
    ```sh
    docker exec habbiton_bot poetry run python -m pytest habbiton/tests/tests.py
    ```