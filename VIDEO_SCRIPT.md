# Slide-led presentation recording script

Suggested duration: 7 to 9 minutes. Speak from the slides, then show the actual console. Replace uncertain statements with what you have actually verified. Record your own voice and show the terminal output clearly. Upload the final video to bilibili and paste the real URL into the report cover.

## Slide 1 — Introduction — 20 seconds

Hello, my name is Wang Hao. My project is a small supermarket point-of-sale system. It covers cash sales and original-receipt returns. I used object-oriented analysis and design to connect requirements, UML models and a runnable implementation.

## Slide 2 — Scope — 30 seconds

The cashier enters products, takes cash and receives a receipt with change. For a return, the system finds the original sale and refunds the original price. I assume tax-inclusive CNY prices and a 30-day return period. The return period is a project assumption. Authentication, electronic payment and physical printer integration are outside this implementation.

## Slides 3 and 4 — Agile plan — 45 seconds

My proposed plan uses two three-day sprints. The first delivers a complete cash-sale increment. The second adds return rules and the submission materials. The backlog contains 32 story points. The burndown chart shows ideal planned lines only. I would record actual remaining work daily and use review feedback to revise the next sprint. I am presenting an individual project and do not claim group activities or historical sprint measurements.

## Slide 5 — Process Sale — 35 seconds

The cashier starts a sale and enters each product with its quantity. The POS shows the running total. When item entry ends, the cashier enters the cash amount. The system validates sufficient cash and stock, then saves the sale and payment and updates stock in one transaction. The receipt shows the total and change. This scenario adapts the detailed Process Sale example in Larman's textbook to the cash-only assignment scope.

## Slide 6 — Handle Returns — 40 seconds

The return starts with the original receipt. The cashier enters the returned items and decides whether each item is resalable. The system checks the date and the quantity still available to return. It uses the original price, so a later catalog price change cannot alter the refund. The return record, refund amount and inventory changes commit together. This elaborates the textbook's brief return scenario using the same analysis method.

## Slides 7 and 8 — Models and architecture — 50 seconds

The domain model separates a sale from its line items and product descriptions. A return refers to the original sale and its original lines. This preserves the connection needed to prevent over-refunds. The logical architecture separates console presentation, application coordination, domain objects and SQLite persistence. The small teaching implementation keeps these logical parts in one source module. The domain calculations do not depend on console input.

## Slide 9 — Responsibilities — 40 seconds

PosController receives system events. Sale creates its line items. Each line knows its own quantity and price, so it calculates its subtotal. Sale and Return calculate totals from those subtotals. These decisions follow Controller, Creator and Information Expert. A database transaction prevents partial updates, and a confirmed request token prevents an exact retry from recording another refund.

## Slides 10 and 11 — Live demonstration — 2 to 3 minutes

Switch to a terminal in the project folder and run:

```powershell
python pos.py --demo
```

Explain the actual output. The two milk items cost 13 yuan, and bread costs 8 yuan. The total is 21 yuan, so 30 yuan cash gives 9 yuan change. Milk stock falls from 20 to 18. A one-milk return refunds 6.50 yuan and restores stock to 19. Retrying the same return token gives the same receipt. An attempt to return two more milk items is rejected because only one remains returnable.

Then demonstrate the interactive interface if time allows:

```text
python pos.py --db video_demo.db
catalog
new
add MILK 2
add BREAD 1
total
pay 30.00
```

Copy your own sale ID from that run. Enter `return`, paste that ID, enter `MILK 1 yes`, then `done`, then `yes`. Show the displayed refund receipt. Enter `catalog` to show the resulting stock. Enter `find YOUR_RECEIPT_ID` to show purchased and already-returned quantities. Enter `quit` to exit. Use a new database filename for a fresh demonstration rather than claiming that an old database begins with initial stock.

## Slide 12 — Tests — 30 seconds

Run:

```powershell
python -m unittest discover -s tests -v
```

The 18 tests check normal totals and refunds, insufficient cash, rollback across multiple stock updates, original prices, excessive returns, damaged goods, the 30-day boundary, repeat requests and persistence after reopening. Mention only the result shown by your actual run.

## Slides 13 and 14 — Completion and references — 30 seconds

The project includes the report, UML, implementation, tests, slides and quiz answers. My main reference is Larman's Applying UML and Patterns, third edition, together with the supplied assignment. Future work could add cashier authentication, physical receipts and payment adapters. Thank you.

## Final recording checklist

- Show the slides and live console, not the report pages as the main presentation.
- Make sure text and audio remain clear in the recorded video.
- Capture only genuine Git history and actual GitHub branches if you show them.
- Upload the video, verify the playback link, update the cover and export the final report PDF again.
