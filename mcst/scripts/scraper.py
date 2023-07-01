import typing as t

import asyncio

from requests import Session as HttpSession
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session

from mcst.database.engine import ENGINE
from mcst.database.models import Server



class MinecraftServerScrapper:
    url_template: t.Optional[str] = None
    """URL template containing a `{page}` variable, e. g.: `https://someserverlist.com/page/{page}` (`page` is passed `MinecraftServerScrapper.page`)."""

    source: str = 'unknown'
    """Source that the server was scraped from."""


    def __init__(self) -> None:
        if self.url_template is None:
            raise ValueError("`url_template` must not be `None`.")
            
        if '{page}' not in self.url_template:
            raise ValueError("`{page}` variable is not present in `url_template`.")


        self.page = 1
        """Current page number."""

        self.http_session = HttpSession()
        self.http_session.headers = {
            "upgrade-insecure-requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-ch-ua": '".Not-A.Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-site": "none",
            "sec-fetch-mod": "",
            "sec-fetch-user": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "bg-BG,bg;q=0.9,en-US;q=0.8,en;q=0.7"
        }


    async def update_soup(self) -> None:
        """
            Updates the BeautifulSoup HTML with a new one by fetching the current page number.
        """

        if self.url_template is None:
            raise ValueError("`url_template` must not be `None`.")

        url = self.url_template.format(page=self.page)
        with self.http_session.get(url) as response:
            self.soup = BeautifulSoup(response.text, 'html.parser')


    def get_max_pages(self) -> int:
        """
            Obtains the last page number from the server list pagination.
        """

        raise NotImplementedError


    def get_servers(self) -> list[dict[str, t.Any]]:
        """
            Yields all server data from current markup
        """

        raise NotImplementedError


    async def scrap_servers(self, verbose: bool=True) -> None:
        """
            The main function - saves lists of all servers if `self.page < self.max_pages`.

            - `verbose` - `print`s the servers
        """

        await self.update_soup()
        max_pages = self.get_max_pages()

        with Session(ENGINE) as session:
            try:
                while self.page < max_pages:
                    for server in self.get_servers():
                        session.merge(Server(**server))

                        if verbose:
                            print(server)
                    
                    print("Committing...")
                    session.commit()


                    self.page += 1
                    await self.update_soup()

                    if verbose and self.url_template is not None:
                        print(f"URL: {self.url_template.format(page=self.page)} / {max_pages}")

            except KeyboardInterrupt:
                print("Committing...")
                session.commit()


            print("OK!")





class MinecraftServers_org_Scrapper(MinecraftServerScrapper):
    url_template = "https://minecraftservers.org/index/{page}"
    source = "https://minecraftservers.org"


    def get_max_pages(self) -> int:
        last_element = self.soup.select_one('#main > .pagination > ul > li:last-child > a')
        href: str = last_element.get('href', default='/1') # type: ignore

        return int(href.split('/')[-1])


    def get_servers(self) -> list[dict[str, t.Any]]:
        all_servers: list[dict[str, t.Any]] = []

        table_rows = self.soup.select('#main > .container > table:last-child > tbody > tr')
        if not table_rows:
            raise RuntimeError(f"No table element.")


        for table_row in table_rows:
            server_name_element = table_row.select_one('.server-name > a')
            ip_port_element = table_row.select_one('.server-ip .copy-action')

            if server_name_element is None or ip_port_element is None:
                raise RuntimeError('Server name `<a>` or `ip_port` is `None`.')


            ip_port: str = ip_port_element.get('data-clipboard-text') # type: ignore

            if ':' not in ip_port:
                ip_port = f"{ip_port}:25565"


            all_servers.append(dict(
                name=server_name_element.text,
                ip_port=ip_port.lower(),
                source=f"{self.source}{server_name_element.get('href')}",
                type='java'
            ))


        return all_servers





async def scrap_all():
    await asyncio.gather(*[
        MinecraftServers_org_Scrapper().scrap_servers()
    ])



if __name__ == '__main__':
    with asyncio.Runner() as runner:
        runner.run(scrap_all())
