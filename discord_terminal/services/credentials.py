import argparse
import re


class CredentialStore:
    def __init__(self, path):
        self.path = path

    def tokens(self):
        if not self.path.exists():
            return []
        content = self.path.read_text(encoding="utf-8")
        blocks = re.findall(r"---\s*(.*?)\s*(?=---|$)", content, re.DOTALL)
        tokens = []
        for block in blocks:
            token_match = re.search(r"Token:\s*(.+)", block)
            name_match = re.search(r"Displayname:\s*(.+)", block)
            user_match = re.search(r"Username:\s*(.+)", block)
            if token_match:
                tokens.append(
                    {
                        "token": token_match.group(1).strip(),
                        "displayname": (
                            name_match.group(1).strip() if name_match else ""
                        ),
                        "username": (
                            user_match.group(1).strip() if user_match else ""
                        ),
                    }
                )
        return tokens

    def select(self, index_or_name=None):
        tokens = self.tokens()
        if not tokens:
            return None
        if index_or_name is None:
            return tokens[0]["token"]
        if index_or_name.isdigit():
            index = int(index_or_name)
            if 0 <= index < len(tokens):
                return tokens[index]["token"]
            return None
        name = index_or_name.lower()
        for token in tokens:
            if name in (
                token["displayname"].lower(),
                token["username"].lower(),
            ):
                return token["token"]
        return None


class ArgumentParser:
    def __init__(self, account_name):
        self.parser = argparse.ArgumentParser(
            description="Discord terminal client bootstrapper",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        self.parser.add_argument(
            "-s",
            "--select",
            help="Select token from {} by index or Displayname/Username".format(
                account_name
            ),
            metavar="INDEX_OR_NAME",
        )
        self.parser.add_argument(
            "-t",
            "--token",
            help="Login using a raw Discord token",
            metavar="TOKEN",
        )

    def parse(self, argv):
        return self.parser.parse_args(argv)
