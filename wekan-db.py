# TODO:
#   * user ID

from typing import List, Optional, Tuple

import pymongo
from pymongo.collection import Collection
import typer
from attrdict import AttrDict

app = typer.Typer()

server_host = "localhost"
server_port = 27019


class ADict(AttrDict):
    @property
    def id(self):
        return self["_id"]


@app.callback()
def callback(host: str = "localhost", port: int = 27017):
    global server_host
    global server_port

    server_host = host
    server_port = port


def find_boards(boards: Collection, title: str) -> List[AttrDict]:
    print(f"Finding board {title!r}...", end="")
    result = list(boards.find({"archived": False, "title": title}))
    print(", ".join(board["_id"] for board in result))
    return result


def find_lists(lists: Collection, board_id: str, title: str) -> List[AttrDict]:
    print(f"Finding list {title!r} in board {board_id}...", end="")
    result = list(lists.find({"archived": False, "boardId": board_id, "title": title}))
    print(", ".join(document["_id"] for document in result))
    return result


def find_boards_lists(boards: Collection, lists: Collection, board_title: str, list_title: str)\
        -> List[Tuple[AttrDict, AttrDict]]:
    return [(board, list_)
            for board in find_boards(boards, board_title)
            for list_ in find_lists(lists, board.id, list_title)]


def count_cards(cards: Collection, list_id: str) -> int:
    return cards.count_documents({"archived": False, "listId": list_id})


def find_swimlane(swimlanes: Collection, board_id: str) -> Optional[AttrDict]:
    print(f"Finding a swimlane in board {board_id}...", end="")
    result = swimlanes.find_one({"archived": False, "boardId": board_id})
    print(result["_id"] if result is not None else "not found")
    return result


@app.command()
def move_cards(from_board_title: str, from_list_title: str, to_board_title: str, to_list_title: str,
               merge_source: bool = False, merge_target: bool = False):
    client = pymongo.MongoClient(server_host, server_port, document_class=ADict)

    db = client["wekan"]

    from_boards_lists = find_boards_lists(db["boards"], db["lists"], from_board_title, from_list_title)
    if len(from_boards_lists) == 0:
        print(f"No list named {from_list_title!r} in board(s) {from_board_title!r}.")
        raise typer.Exit(1)
    elif len(from_boards_lists) > 1 and not merge_source:
        print(f"Multiple lists named {from_list_title!r} in board(s) {from_board_title!r}."
              " Specify --merge-source to merge.")
        raise typer.Exit(1)

    to_boards_lists = find_boards_lists(db["boards"], db["lists"], to_board_title, to_list_title)
    if len(to_boards_lists) == 0:
        print(f"No list named {to_list_title!r} in board(s) {to_board_title!r}.")
        raise typer.Exit(1)
    elif len(to_boards_lists) > 1:
        print(f"Ambiguous target {to_list_title!r} in board(s) {to_board_title!r}")
        raise typer.Exit(1)
    to_board, to_list = to_boards_lists[0]

    existing_card_count = count_cards(db["cards"], to_list.id)
    if existing_card_count > 0 and not merge_target:
        print(f"The target list is not empty. Specify --merge-target to merge.")
        raise typer.Exit(1)

    to_swimlane = find_swimlane(db["swimlanes"], to_board.id)

    total_moved = 0
    for from_board, from_list in from_boards_lists:
        result = db["cards"].update_many(filter={"archived": False,
                                                 "boardId": from_board.id,
                                                 "listId": from_list.id},
                                         update={"$set": {"boardId": to_board.id,
                                                          "swimlaneId": to_swimlane.id,
                                                          "listId": to_list.id}})
        total_moved += result.modified_count

    print(f"{total_moved} cards moved, {existing_card_count} already there")


if __name__ == "__main__":
    app()
