from typing import List, Optional

import pymongo
from pymongo.collection import Collection
import typer
from attrdict import AttrDict

app = typer.Typer()

server_host = "localhost"
server_port = 27019


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
    print(f"Finding list {title!r} in board {board_id!r}...", end="")
    result = list(lists.find({"archived": False, "boardId": board_id, "title": title}))
    print(", ".join(document["_id"] for document in result))
    return result


def find_swimlane(swimlanes: Collection, board_id: str) -> Optional[AttrDict]:
    print(f"Finding a swimlane in board {board_id!r}...", end="")
    result = swimlanes.find_one({"archived": False, "boardId": board_id})
    print(result["_id"] if result is not None else "not found")
    return result


@app.command()
def move_cards(from_board: str, from_list: str, to_board: str, to_list: str):
    client = pymongo.MongoClient(server_host, server_port, document_class=AttrDict)

    db = client["wekan"]

    from_boards = find_boards(db["boards"], from_board)
    assert len(from_boards) == 1
    from_board = from_boards[0]

    to_boards = find_boards(db["boards"], to_board)
    assert len(to_boards) == 1
    to_board = to_boards[0]

    from_lists = find_lists(db["lists"], from_board["_id"], from_list)
    to_lists   = find_lists(db["lists"], to_board  ["_id"], to_list)

    assert len(from_lists) == 1
    assert len(to_lists) == 1

    from_list = from_lists[0]
    to_list = to_lists[0]

    to_swimlane = find_swimlane(db["swimlanes"], to_board["_id"])

    result = db["cards"].update_many(filter={"archived": False,
                                             "boardId": from_board["_id"],
                                             "listId": from_list["_id"]},
                                     update={"$set": {"boardId": to_board["_id"],
                                                      "swimlaneId": to_swimlane["_id"],
                                                      "listId": to_list["_id"]}})
    print(f"{result.modified_count} cards moved")

    # TODO user ID


if __name__ == "__main__":
    app()
