import unittest
from datetime import date,timedelta
from pos import SQLiteRepository,PosController,PosError,money

class PosTests(unittest.TestCase):
    def setUp(self):
        self.repo=SQLiteRepository(':memory:'); self.repo.seed()
        self.pos=PosController(self.repo,today=lambda:date(2026,10,19))
    def tearDown(self): self.repo.close()
    def sell(self,count=2,token='sale'):
        self.pos.make_new_sale(); self.pos.enter_item('MILK',count); self.pos.end_sale()
        return self.pos.make_cash_payment('100.00',token)
    def stock(self): return self.repo.db.execute("SELECT stock FROM products WHERE sku='MILK'").fetchone()[0]
    def test_sale_total_change_and_stock(self):
        s=self.sell(); self.assertEqual((s['total'],s['change'],self.stock()),('13.00','87.00',18))
    def test_underpayment_has_no_effect(self):
        self.pos.make_new_sale(); self.pos.enter_item('MILK',2); self.pos.end_sale()
        with self.assertRaises(PosError): self.pos.make_cash_payment('1.00','bad')
        self.assertEqual(self.stock(),20); self.assertEqual(self.repo.db.execute('SELECT count(*) FROM sales').fetchone()[0],0)
    def test_insufficient_stock_rolls_back_all_lines(self):
        self.pos.make_new_sale(); self.pos.enter_item('BREAD',1); self.pos.enter_item('MILK',21); self.pos.end_sale()
        with self.assertRaises(PosError): self.pos.make_cash_payment('200','bad')
        self.assertEqual(self.stock(),20); self.assertEqual(self.repo.db.execute("SELECT stock FROM products WHERE sku='BREAD'").fetchone()[0],15)
        self.assertEqual(self.repo.db.execute('SELECT count(*) FROM sales').fetchone()[0],0)
    def test_partial_return_and_original_price(self):
        s=self.sell(); self.repo.db.execute("UPDATE products SET price=900 WHERE sku='MILK'")
        r=self.pos.complete_return(s['id'],[('MILK',1,True)],'r')
        self.assertEqual((r['cash_refund'],self.stock()),('6.50',19))
    def test_over_return_rejected(self):
        s=self.sell(); self.pos.complete_return(s['id'],[('MILK',1,True)],'r')
        with self.assertRaises(PosError): self.pos.complete_return(s['id'],[('MILK',2,True)],'r2')
        self.assertEqual(self.stock(),19)
    def test_return_retry_is_idempotent(self):
        s=self.sell(); r=self.pos.complete_return(s['id'],[('MILK',1,True)],'r')
        self.assertEqual(r,self.pos.complete_return(s['id'],[('MILK',1,True)],'r')); self.assertEqual(self.stock(),19)
    def test_sale_retry_and_new_token(self):
        s=self.sell(); self.assertEqual(s,self.pos.make_cash_payment('100','sale'))
        with self.assertRaises(PosError): self.pos.make_cash_payment('100','other')
        self.assertEqual(self.stock(),18)
    def test_token_conflict(self):
        s=self.sell(); self.pos.complete_return(s['id'],[('MILK',1,True)],'r')
        with self.assertRaises(PosError): self.pos.complete_return(s['id'],[('MILK',2,True)],'r')
    def test_damaged_goods_not_restocked(self):
        s=self.sell(); self.pos.complete_return(s['id'],[('MILK',1,False)],'r'); self.assertEqual(self.stock(),18)
    def test_missing_receipt_and_unpurchased_sku(self):
        with self.assertRaises(PosError): self.pos.complete_return('missing',[('MILK',1,True)],'r')
        s=self.sell()
        with self.assertRaises(PosError): self.pos.complete_return(s['id'],[('APPLE',1,True)],'r2')
    def test_expired_receipt(self):
        s=self.sell(); self.pos.today=lambda:date(2026,11,19)
        with self.assertRaises(PosError): self.pos.complete_return(s['id'],[('MILK',1,True)],'r')
    def test_thirty_day_boundary(self):
        s=self.sell(); self.pos.today=lambda:date(2026,11,18)
        self.assertEqual(self.pos.complete_return(s['id'],[('MILK',1,True)],'r')['cash_refund'],'6.50')
    def test_invalid_quantities_and_money(self):
        self.pos.make_new_sale()
        for q in [0,-1,1.5,True]:
            with self.assertRaises(PosError): self.pos.enter_item('MILK',q)
        for m in ['NaN','Infinity','-1','1.001']:
            with self.assertRaises(PosError): money(m)
    def test_duplicate_sku_rejected(self):
        s=self.sell()
        with self.assertRaises(PosError): self.pos.complete_return(s['id'],[('MILK',1,True),('MILK',1,True)],'r')
    def test_cancel_has_no_inventory_effect(self):
        self.pos.make_new_sale(); self.pos.enter_item('MILK',1); self.pos.cancel_sale(); self.assertEqual(self.stock(),20)
    def test_unknown_item(self):
        self.pos.make_new_sale()
        with self.assertRaises(PosError): self.pos.enter_item('UNKNOWN',1)
    def test_empty_sale(self):
        self.pos.make_new_sale()
        with self.assertRaises(PosError): self.pos.end_sale()
    def test_persistence_after_reopen(self):
        import tempfile,os
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as directory:
            path=os.path.join(directory,'test.db'); repo=SQLiteRepository(path); repo.seed(); pos=PosController(repo)
            pos.make_new_sale(); pos.enter_item('MILK',1); pos.end_sale(); receipt=pos.make_cash_payment('10','p'); repo.close()
            repo=SQLiteRepository(path); self.assertEqual(PosController(repo).find_sale(receipt['id'])['total'],'6.50'); repo.close()

if __name__=='__main__': unittest.main()

