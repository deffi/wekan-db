from typing import List

import pymongo
from pymongo.collection import Collection
import typer

app = typer.Typer()


@app.callback()
def callback():
    pass


def find_board_id(boards: Collection, title: str) -> str:
    print(f"Finding board {title!r}...", end="")
    documents = list(boards.find({"archived": False, "title": title}, {"_id": True}))
    assert len(documents) == 1
    board_id = documents[0]["_id"]
    print(f"{board_id}")
    return board_id


def find_list_ids(lists: Collection, board_id: str, title: str, *, ensure_unique: bool) -> List[str]:
    print(f"Finding list {title!r} in board {board_id!r}...", end="")
    documents = list(lists.find({"archived": False, "boardId": board_id, "title": title}, {"_id": True}))

    # TODO use cursor methods instead of converting to list?
    assert len(documents) > 0
    if ensure_unique:
        assert len(documents) == 1

    list_ids = [document["_id"] for document in documents]
    print(", ".join(list_ids))
    return list_ids


def find_list_id(lists: Collection, board_id: str, title: str) -> str:
    return find_list_ids(lists, board_id, title, ensure_unique=True)[0]


def find_first_swimlane_id(swimlanes: Collection, board_id: str) -> str:
    print(f"Finding a swimlane in board {board_id!r}...", end="")
    result = swimlanes.find_one({"archived": False, "boardId": board_id})
    assert result is not None
    swimlane_id = result["_id"]
    print(swimlane_id)
    return swimlane_id


@app.command()
def move_cards(from_board: str, from_list: str, to_board: str, to_list: str):
    client = pymongo.MongoClient("localhost", 27019)

    db = client["wekan"]

    boards = db["boards"]
    from_board_id = find_board_id(boards, from_board)
    to_board_id = find_board_id(boards, to_board)

    lists = db["lists"]
    from_list_id = find_list_id(lists, from_board_id, from_list)
    to_list_id = find_list_id(lists, to_board_id, to_list)

    swimlanes = db["swimlanes"]
    to_swimlane_id = find_first_swimlane_id(swimlanes, to_board_id)

    cards = db["cards"]
    filter_ = {"archived": False, "boardId": from_board_id, "listId": from_list_id}
    update = {"$set": {"boardId": to_board_id, "swimlaneId": to_swimlane_id, "listId": to_list_id}}
    result = cards.update_many(filter_, update)
    print(f"{result.modified_count} cards moved")

    # TODO user ID


if __name__ == "__main__":
    app()
