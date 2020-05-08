"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.assign_login(decoded)
                self.transport.write(
                    f"Привет, {self.login}!".encode()
                )
                self.send_history()
        else:
            self.send_message(decoded)

    def assign_login(self, decoded):
        login = decoded.replace("login:", "").replace("\r\n", "")
        self.check_login(login)
        self.login = login

    def check_login(self, login):
        for client in self.server.clients:
            if client.login == login:
                self.transport.write(
                    f"Логин {login} занят, попробуйте другой".encode()
                )
                self.transport.close()
                break

    def send_history(self):
        for encoded in self.server.history:
            self.transport.write(encoded)

    def send_message(self, message):
        format_string = f"\n<{self.login}> {message}"
        encoded = format_string.encode()

        self.save_to_history(encoded)
        self.send_to_clients(encoded)

    def save_to_history(self, encoded):
        self.server.history.append(encoded)

        if len(self.server.history) > Server.HISTORY_MAX_SIZE:
            self.server.history.pop(0)

    def send_to_clients(self, encoded):
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    HISTORY_MAX_SIZE = 10

    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")