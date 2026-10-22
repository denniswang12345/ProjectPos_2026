# ProjectPos 2026

A small cash POS for the Software Engineering Practice assignment.

Author: Wang Hao (汪浩). One actual contributor; no group collaboration is claimed.
Repository: https://github.com/denniswang12345/ProjectPos_2026

## Run

Requires Python 3.10 or later. No pip packages are needed.

```powershell
python pos.py --demo
python pos.py
python -m unittest discover -s tests -v
```

On Windows, `py` can replace `python` if that is how Python is installed. The demo runs against an isolated in-memory database. The interactive console creates `pos.db` in the working directory. `python pos.py --db practice.db` selects another file.

## Interactive sale

```text
catalog
new
add MILK 2
add BREAD 1
total
pay 30.00
```

The total is CNY 21.00 and change CNY 9.00. Copy the sale ID printed on your receipt.

## Interactive return

Enter `return`, then your own receipt ID. Enter `MILK 1 yes`, then `done`, then `yes` to confirm. The final `yes` confirms that the cashier will make the cash refund; the earlier `yes` means the inspected product may be restocked. Enter `no` for a damaged accepted item that should not increase saleable inventory.

Other commands: `find RECEIPT_ID`, `cancel`, `quit`. Product identifiers are MILK, BREAD and APPLE.

## Design and rules

- Positive integer quantities, integer-cent money and tax-inclusive CNY prices.
- Sale and stock updates are atomic; a failed update rolls back the whole operation.
- Returns require an original receipt within 30 days, inclusive, and cannot exceed remaining purchased quantities.
- Refunds use the original price even if the catalog price changes.
- Only resalable goods are restocked.
- Controller operations accept a unique token so exact confirmed requests can be retried without a second recorded transaction. The CLI generates fresh tokens. The isolated demo exercises a deliberate retry.
- Authentication, a physical cash drawer balance, printer drivers and noncash payments are outside scope.

`pos.py` contains logical presentation, application, domain and persistence components in one small module. The UML package diagram represents these logical boundaries rather than physical Python packages. The controller currently uses repository.db for transaction SQL; this is a teaching simplification, not a full repository abstraction.

## Files

- `pos.py`: complete application and isolated demo
- `tests/test_pos.py`: 18 invariant and scenario tests
- `docs/*.puml`: editable PlantUML source for eight UML views
- `docs/*.png`: rendered UML diagrams and actual console transcript image
- `submission/`: final report, slides and quiz answers
- `GIT_COMMAND_HISTORY.txt`: original PowerShell remote-workflow transcript
- `docs/screenshots/`: original student-captured execution and GitHub evidence
- `VIDEO_URL.txt`: recorded presentation and repository links

## Recorded presentation

https://www.bilibili.com/video/BV1xgnp64E3X/

The final report contains the video URL and eight original execution and Git evidence screenshots. The personal development branch is retained after merging into main. The agile plan and ideal burndown are planning artifacts; no historical daily sprint measurements or group meetings are claimed.

## Recorded presentation

https://www.bilibili.com/video/BV1xgnp64E3X/

The final report contains the video URL and eight original execution and Git evidence screenshots. The personal development branch is retained after merging into main. The agile plan and ideal burndown are planning artifacts; no historical daily sprint measurements or group meetings are claimed.
