"""Small cash POS. Python 3.10+, standard library only."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import sqlite3
import uuid

class PosError(ValueError):
    pass

def money(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal('0.01')):
            raise PosError('Use a nonnegative amount with at most two decimal places.')
        return int(amount * 100)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise PosError('Invalid money amount.') from error

def fmt(cents):
    return f'{cents / 100:.2f}'

def quantity(value):
    if type(value) is not int or value <= 0:
        raise PosError('Quantity must be a positive integer.')
    return value

@dataclass(frozen=True)
class ProductDescription:
    sku: str
    description: str
    price_cents: int

@dataclass
class SalesLineItem:
    product: ProductDescription
    quantity: int
    @property
    def subtotal(self):
        return self.product.price_cents * self.quantity

@dataclass
class Sale:
    lines: dict
    state: str = 'OPEN'
    @property
    def total(self):
        return sum(line.subtotal for line in self.lines.values())
    def add(self, product, count):
        if self.state != 'OPEN':
            raise PosError('Sale is no longer open.')
        quantity(count)
        if product.sku in self.lines:
            self.lines[product.sku].quantity += count
        else:
            self.lines[product.sku] = SalesLineItem(product, count)

@dataclass(frozen=True)
class ReturnLineItem:
    sku: str
    quantity: int
    original_price_cents: int
    restock: bool
    @property
    def subtotal(self):
        return self.quantity * self.original_price_cents

@dataclass
class Return:
    original_sale_id: str
    lines: list
    @property
    def total(self):
        return sum(line.subtotal for line in self.lines)

class SQLiteRepository:
    def __init__(self, path='pos.db'):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS products(sku TEXT PRIMARY KEY, name TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>=0), stock INTEGER NOT NULL CHECK(stock>=0));
        CREATE TABLE IF NOT EXISTS sales(id TEXT PRIMARY KEY, sold_on TEXT NOT NULL, total INTEGER NOT NULL, paid INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sale_lines(sale_id TEXT REFERENCES sales(id), sku TEXT REFERENCES products(sku), qty INTEGER NOT NULL, price INTEGER NOT NULL, returned INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(sale_id,sku), CHECK(returned>=0 AND returned<=qty));
        CREATE TABLE IF NOT EXISTS returns(id TEXT PRIMARY KEY, sale_id TEXT REFERENCES sales(id), returned_on TEXT NOT NULL, total INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS return_lines(return_id TEXT REFERENCES returns(id), sku TEXT REFERENCES products(sku), qty INTEGER NOT NULL, price INTEGER NOT NULL, restock INTEGER NOT NULL, PRIMARY KEY(return_id,sku));
        CREATE TABLE IF NOT EXISTS operations(token TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, receipt TEXT NOT NULL);
        ''')
    def seed(self):
        self.db.executemany('INSERT OR IGNORE INTO products VALUES(?,?,?,?)', [('MILK','Milk 1L',650,20),('BREAD','Bread',800,15),('APPLE','Apple pack',1200,10)])
    def catalog(self):
        return self.db.execute('SELECT sku,name,price,stock FROM products ORDER BY sku').fetchall()
    def product(self, sku):
        row = self.db.execute('SELECT sku,name,price FROM products WHERE sku=?',(sku,)).fetchone()
        if not row:
            raise PosError('Unknown product identifier.')
        return ProductDescription(*row)
    def close(self):
        self.db.close()

class PosController:
    RETURN_DAYS = 30
    def __init__(self, repository, today=date.today):
        self.repo, self.today, self.current_sale = repository, today, None
    def make_new_sale(self):
        if self.current_sale and self.current_sale.state in ('OPEN','ENDED'):
            raise PosError('Finish or cancel the current sale first.')
        self.current_sale = Sale({})
    def enter_item(self, sku, count):
        if not self.current_sale:
            raise PosError('Start a sale first.')
        self.current_sale.add(self.repo.product(sku), count)
        return self.current_sale.total
    def end_sale(self):
        if not self.current_sale or self.current_sale.state != 'OPEN' or not self.current_sale.lines:
            raise PosError('An open nonempty sale is required.')
        self.current_sale.state = 'ENDED'
        return self.current_sale.total
    def cancel_sale(self):
        self.current_sale = None
    def _atomic(self, token, fingerprint, action):
        if not isinstance(token,str) or not token.strip():
            raise PosError('Operation token is required.')
        db = self.repo.db
        db.execute('BEGIN IMMEDIATE')
        try:
            previous = db.execute('SELECT fingerprint,receipt FROM operations WHERE token=?',(token,)).fetchone()
            if previous:
                if previous[0] != fingerprint:
                    raise PosError('Operation token was used for a different request.')
                result = json.loads(previous[1])
            else:
                result = action(db)
                db.execute('INSERT INTO operations VALUES(?,?,?)',(token,fingerprint,json.dumps(result)))
            db.execute('COMMIT')
            return result
        except Exception:
            db.execute('ROLLBACK')
            raise
    def make_cash_payment(self, tendered, token):
        sale = self.current_sale
        if not sale or sale.state not in ('ENDED','PAID'):
            raise PosError('End the sale before payment.')
        paid = money(tendered)
        fingerprint = json.dumps(['sale',[(k,v.quantity,v.product.price_cents) for k,v in sorted(sale.lines.items())],paid])
        if sale.state == 'PAID':
            previous = self.repo.db.execute('SELECT fingerprint,receipt FROM operations WHERE token=?',(token,)).fetchone()
            if previous and previous[0] == fingerprint:
                return json.loads(previous[1])
            raise PosError('Sale has already been paid.')
        def save(db):
            if paid < sale.total:
                raise PosError('Insufficient cash tendered.')
            sale_id = 'S-' + uuid.uuid4().hex[:12]
            db.execute('INSERT INTO sales VALUES(?,?,?,?)',(sale_id,self.today().isoformat(),sale.total,paid))
            for line in sale.lines.values():
                changed = db.execute('UPDATE products SET stock=stock-? WHERE sku=? AND stock>=?',(line.quantity,line.product.sku,line.quantity)).rowcount
                if changed != 1:
                    raise PosError('Insufficient stock for '+line.product.sku)
                db.execute('INSERT INTO sale_lines(sale_id,sku,qty,price) VALUES(?,?,?,?)',(sale_id,line.product.sku,line.quantity,line.product.price_cents))
            return {'type':'SALE','id':sale_id,'date':self.today().isoformat(),'total':fmt(sale.total),'cash':fmt(paid),'change':fmt(paid-sale.total),'lines':[{'sku':x.product.sku,'qty':x.quantity,'unit_price':fmt(x.product.price_cents)} for x in sale.lines.values()]}
        result = self._atomic(token,fingerprint,save)
        sale.state = 'PAID'
        return result
    def find_sale(self, sale_id):
        row = self.repo.db.execute('SELECT id,sold_on,total FROM sales WHERE id=?',(sale_id,)).fetchone()
        if not row:
            raise PosError('Original receipt not found.')
        lines = self.repo.db.execute('SELECT sku,qty,price,returned FROM sale_lines WHERE sale_id=?',(sale_id,)).fetchall()
        return {'id':row[0],'date':row[1],'total':fmt(row[2]),'lines':[{'sku':s,'purchased':q,'unit_price':fmt(p),'already_returned':r} for s,q,p,r in lines]}
    def complete_return(self, sale_id, requested, token):
        """requested: [(sku, quantity, restock_bool)]. Cashier has inspected goods."""
        if not requested:
            raise PosError('Select at least one returned item.')
        normalized=[]
        for sku,count,restock in requested:
            quantity(count)
            if type(restock) is not bool:
                raise PosError('Restock must be true or false.')
            normalized.append((sku,count,restock))
        if len({s for s,_,_ in normalized}) != len(normalized):
            raise PosError('Enter each returned SKU once.')
        fingerprint=json.dumps(['return',sale_id,sorted(normalized)])
        def save(db):
            original=self.find_sale(sale_id)
            age=(self.today()-date.fromisoformat(original['date'])).days
            if age<0 or age>self.RETURN_DAYS:
                raise PosError('Receipt is outside the 30-day return period.')
            original_lines={x['sku']:x for x in original['lines']}
            lines=[]
            for sku,count,restock in normalized:
                old=original_lines.get(sku)
                if not old or count>old['purchased']-old['already_returned']:
                    raise PosError('Item not purchased or return quantity exceeds remaining allowance.')
                lines.append(ReturnLineItem(sku,count,money(old['unit_price']),restock))
            transaction=Return(sale_id,lines)
            return_id='R-'+uuid.uuid4().hex[:12]
            db.execute('INSERT INTO returns VALUES(?,?,?,?)',(return_id,sale_id,self.today().isoformat(),transaction.total))
            for line in lines:
                db.execute('UPDATE sale_lines SET returned=returned+? WHERE sale_id=? AND sku=?',(line.quantity,sale_id,line.sku))
                db.execute('INSERT INTO return_lines VALUES(?,?,?,?,?)',(return_id,line.sku,line.quantity,line.original_price_cents,int(line.restock)))
                if line.restock:
                    db.execute('UPDATE products SET stock=stock+? WHERE sku=?',(line.quantity,line.sku))
            return {'type':'RETURN','id':return_id,'original_sale':sale_id,'date':self.today().isoformat(),'cash_refund':fmt(transaction.total),'lines':[{'sku':x.sku,'qty':x.quantity,'unit_price':fmt(x.original_price_cents),'restock':x.restock} for x in lines]}
        return self._atomic(token,fingerprint,save)

def print_receipt(receipt):
    print(json.dumps(receipt,indent=2,ensure_ascii=False))

def demo():
    repo=SQLiteRepository(':memory:'); repo.seed(); pos=PosController(repo)
    print('DEMO / isolated in-memory data / currency CNY')
    print('Initial stock',repo.catalog())
    pos.make_new_sale(); print('Scan MILK x2:',fmt(pos.enter_item('MILK',2)))
    print('Scan BREAD x1:',fmt(pos.enter_item('BREAD',1)))
    print('Total:',fmt(pos.end_sale()))
    receipt=pos.make_cash_payment('30.00','demo-sale'); print_receipt(receipt)
    print('Stock after sale',repo.catalog())
    returned=pos.complete_return(receipt['id'],[('MILK',1,True)],'demo-return'); print_receipt(returned)
    print('Retry returns same receipt:',pos.complete_return(receipt['id'],[('MILK',1,True)],'demo-return')['id']==returned['id'])
    try: pos.complete_return(receipt['id'],[('MILK',2,True)],'demo-excess')
    except PosError as error: print('Over-return rejected:',error)
    print('Final stock',repo.catalog()); repo.close()

def interactive(path):
    repo=SQLiteRepository(path); repo.seed(); pos=PosController(repo)
    print('ProjectPos 2026 / Cashier training session / CNY tax-inclusive prices')
    print('Commands: catalog, new, add SKU QTY, total, pay AMOUNT, cancel, find RECEIPT, return, quit')
    while True:
        try:
            parts=input('pos> ').strip().split()
            if not parts: continue
            cmd=parts[0].lower()
            if cmd=='quit': break
            elif cmd=='catalog':
                for sku,name,price,stock in repo.catalog(): print(sku,name,fmt(price),'stock',stock)
            elif cmd=='new': pos.make_new_sale(); print('Sale started')
            elif cmd=='add' and len(parts)==3: print('Running total',fmt(pos.enter_item(parts[1].upper(),int(parts[2]))))
            elif cmd=='total': print('Total',fmt(pos.end_sale()))
            elif cmd=='pay' and len(parts)==2: print_receipt(pos.make_cash_payment(parts[1],uuid.uuid4().hex))
            elif cmd=='cancel': pos.cancel_sale(); print('Cancelled')
            elif cmd=='find' and len(parts)==2: print_receipt(pos.find_sale(parts[1]))
            elif cmd=='return':
                sale_id=input('Original receipt ID: ').strip(); print_receipt(pos.find_sale(sale_id))
                lines=[]
                while True:
                    entry=input('Returned item: SKU QTY yes/no(restock), or done: ').strip().split()
                    if entry==['done']: break
                    if len(entry)!=3 or entry[2].lower() not in ('yes','no'): raise PosError('Use SKU QTY yes/no.')
                    lines.append((entry[0].upper(),int(entry[1]),entry[2].lower()=='yes'))
                if input('Confirm cash refund? yes/no: ').strip().lower()=='yes': print_receipt(pos.complete_return(sale_id,lines,uuid.uuid4().hex))
                else: print('Return cancelled before commit')
            else: print('Unknown command or missing arguments')
        except (PosError,ValueError,sqlite3.Error) as error: print('ERROR:',error)
        except (EOFError,KeyboardInterrupt): break
    repo.close()

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--demo',action='store_true'); parser.add_argument('--db',default='pos.db')
    args=parser.parse_args()
    if args.demo: demo()
    else: interactive(args.db)
