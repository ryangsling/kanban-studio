from app.schemas import BoardData, CardData, ColumnData

SEED_BOARD = BoardData(
    columns=[
        ColumnData(id="col-backlog", title="Backlog", cardIds=["card-1", "card-2"]),
        ColumnData(id="col-discovery", title="Discovery", cardIds=["card-3"]),
        ColumnData(id="col-progress", title="In Progress", cardIds=["card-4", "card-5"]),
        ColumnData(id="col-review", title="Review", cardIds=["card-6"]),
        ColumnData(id="col-done", title="Done", cardIds=["card-7", "card-8"]),
    ],
    cards={
        "card-1": CardData(
            id="card-1",
            title="Align roadmap themes",
            details="Draft quarterly themes with impact statements and metrics.",
        ),
        "card-2": CardData(
            id="card-2",
            title="Gather customer signals",
            details="Review support tags, sales notes, and churn feedback.",
        ),
        "card-3": CardData(
            id="card-3",
            title="Prototype analytics view",
            details="Sketch initial dashboard layout and key drill-downs.",
        ),
        "card-4": CardData(
            id="card-4",
            title="Refine status language",
            details="Standardize column labels and tone across the board.",
        ),
        "card-5": CardData(
            id="card-5",
            title="Design card layout",
            details="Add hierarchy and spacing for scanning dense lists.",
        ),
        "card-6": CardData(
            id="card-6",
            title="QA micro-interactions",
            details="Verify hover, focus, and loading states.",
        ),
        "card-7": CardData(
            id="card-7",
            title="Ship marketing page",
            details="Final copy approved and asset pack delivered.",
        ),
        "card-8": CardData(
            id="card-8",
            title="Close onboarding sprint",
            details="Document release notes and share internally.",
        ),
    },
)
