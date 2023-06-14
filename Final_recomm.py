import pandas as pd
import mysql.connector as sql
from collections import defaultdict
import sys
from operator import itemgetter
import time
import sqlalchemy
from sqlalchemy import create_engine
import credentials 

class RecommendationEngineASS:
    def __init__(self, hostname, database, user, password):
        print("I am in __init__")
        self.hostname = hostname
        self.database = database
        self.user = user
        self.password = password

    def connectDB(self):
        print("Connecting with DB: ")
        self.db_connection = sql.connect(host=self.hostname, database=self.database, user=self.user, password=self.password)
        self.db_cursor = self.db_connection.cursor()

    def getDF(self):
        print("I am in getDF")
        query = """
        SELECT sales_master.sale_number As SalesNo,
 		   contacts_master.customerID AS customerID,
 		   sale_details.quantity AS QtyOrdered,
 		   sale_details.item_id AS ItemID,
 		   lookup_master.lookup_value As Category,
           inventory_master.description_1 AS ProductDesc
 	FROM sale_details
		INNER JOIN sales_master ON sales_master.id = sale_details.sales_master_id
		INNER JOIN contacts_master ON contacts_master.id = sales_master.customer_id
		INNER JOIN inventory_master ON inventory_master.id = sale_details.inventory_id
		LEFT JOIN lookup_master ON lookup_master.id = inventory_master.category_code_id 
AND  lookup_key = 'category_code'
        """
        self.db_cursor.execute(query)

        table_rows = self.db_cursor.fetchall()
        data = pd.DataFrame(table_rows)
        # print(data.head(5))
        # filter df
        # df = pd.read_csv("D://workspace//amitesh//BuyerItemData.csv",  engine = "python")
        #data = df.dropna(axis=0).reset_index(drop=True)
        # print("Data cols")
        # print(data.columns.to_list())

        data.columns = ['OrderID', 'CustomerID', 'QtyOrdered', 'ProductID', 'CategoryID',  'ProductDesc']
        # 'CategoryID']
        data.columns = data.columns.str.strip()
        #print(data.head())
        data = data[(data["CategoryID"] != "DELIVERY") ]
        # print("Rows n Cols ->", data.shape)
        c_data = data.groupby(['CustomerID','ProductID', 'CategoryID', 'OrderID']).size().reset_index(name='Quantity')

        #data.groupby(['CustomerID','ProductID']).size()
        return c_data, data
    
    def find_frequent_itemsets(self, bought_by_users,k_itemsets,min_support):
        print("I am in find_frequent_itemsets")
        counts = defaultdict(int)
        # iterate over all of the users and their products
        for user,product in bought_by_users.items():
            # see whether itemset is a subset of the products or not
            for itemset in k_itemsets:
                if itemset.issubset(product):
                    for other_prchased_product in product-itemset:
                        current_superset = itemset|frozenset((other_prchased_product,))
                        counts[current_superset] += 1
        return dict([(itemset,frequence) for itemset,frequence in counts.items() if frequence >= min_support])

    def insertToDB(self, host, database, user, password, df):
        print("I am in insertToDB")
        # print("Connecting with DB: ")
        '''db_connection = sql.connect(host=host, database=database, user=user, password=password)
        db_cursor = db_connection.cursor()
        
		val = []
        val.append(val1)
        val.append(val2)
        #change table name here
        sql_ = "INSERT INTO recommendation_engine_tmp (if_bought, then_also) VALUES (%s, %s)"
        # print(sql_)
        db_cursor.execute(sql_, tuple(val))

        db_connection.commit()'''
      
        # print(db_cursor.rowcount, "record inserted.")
        a = urllib.parse.quote_plus(password)
        #print("mysql+mysqlconnector://"+ user+":"+a+"@" + host + "/" + database +"?auth_plugin=mysql_native_password")
        db_connection = sqlalchemy.create_engine("mysql+mysqlconnector://"+ user+":"+a+"@" + host + "/" + database +"?auth_plugin=mysql_native_password", echo=True)
        sql_query2 = df.to_sql(name = 'recommendation_engine_tmp',con = db_connection, if_exists = 'replace', index = False ) 
        #print(db_cursor.rowcount, "record inserted.")
        #db_connection.execute("SELECT * FROM recommendation_engine_tmp").fetchall()

        
    def truncTable(self, host, database, user, password, table ="recommendation_engine_tmp"):

        # print("Connecting with DB: ")
        db_connection = sql.connect(host=host, database=database, user=user, password=password)
        db_cursor = db_connection.cursor()

        sql_ = "truncate table recommendation_engine_tmp "
        # print(sql_)
        db_cursor.execute(sql_)

        db_connection.commit()
        

obj = RecommendationEngineASS(credentials.host,  credentials.database, credentials.user, credentials.password)    
obj.connectDB()
c_data, data = obj.getDF()
'''c_data.to_csv('data_new.csv',index=False)
c_data = pd.read_csv('data_new.csv')'''
#c_data = c_data.iloc[:200,:]
c_data= c_data[c_data.CustomerID.isna() == False]
bought_by_users = dict((k, frozenset(v.values)) for k, v in c_data.groupby("CustomerID")["ProductID"])
print(len(bought_by_users))
print(len(c_data))   
num_favor_by_product = c_data[["ProductID","Quantity"]].groupby("ProductID").sum()
num_favor_by_product.sort_values("Quantity",ascending=False)[:5]

frequent_itemsets={}
min_support = 1
     # frequent item set of length 1
frequent_itemsets[1] = dict((frozenset((product_id,)),row['Quantity']) for product_id,row in num_favor_by_product.iterrows() if row['Quantity'] > min_support)
    # print("There are {0} product_id with more than {1} quantity .".format(len(frequent_itemsets[1]),min_support))
for k in range(2,3):
        #Generate k frequent itemsets by k-1 frequent itemsets
    cur_frequent_itemsets = obj.find_frequent_itemsets(bought_by_users,frequent_itemsets[k-1],min_support)
    if len(cur_frequent_itemsets) == 0:
        print("Did not any frequent itemsets of length {}".format(k))
        sys.stdout.flush()
        break
    else:
            # print("I found {} frequent itemsets of length {}".format(len(cur_frequent_itemsets),k))
        sys.stdout.flush()
        frequent_itemsets[k] = cur_frequent_itemsets
    # Frequent itemsets of length 1 do not need
del frequent_itemsets[1]
    # print("Found a total of {} frequent itemsets.".format(sum(len(frequent_item) for frequent_item in frequent_itemsets.values())))

    # Now, we create the association rules.First ,they can ben the candidate rules until tested
candidate_rules = []
for itemset_length,itemset_counts in frequent_itemsets.items():
    for itemset in itemset_counts.keys():
                     # Take one of the items as a conclusion, others as a premise
        for conclusion in itemset:
            premise = itemset - set((conclusion,))
            candidate_rules.append((premise,conclusion))
                # print("There are {} candidate rules in total.".format(len(candidate_rules)))
    # print(candidate_rules[:5])

    # Now,we compute the confidence of each of these rules.
correct_counts = defaultdict(int)
incorrect_counts = defaultdict(int)
for user,reviews in bought_by_users.items():
    for candidate_rule in candidate_rules:
        premise,conclusion = candidate_rule
        if premise.issubset(reviews):
            if conclusion in reviews:
                correct_counts[candidate_rule] += 1
            else:
                incorrect_counts[candidate_rule] += 1
rule_confidence = {candidate_rule: correct_counts[candidate_rule] / float(correct_counts[candidate_rule] + incorrect_counts[candidate_rule])
                    for candidate_rule in candidate_rules}
    # set the min_confidence
min_confidence = 0.4
    # filter out the poor rules
rule_confidence = {rule: confidence for rule,confidence in rule_confidence.items() if confidence > min_confidence}
    # print(len(rule_confidence))
sort_confidence = sorted(rule_confidence.items(),key=itemgetter(1),reverse = True)
for index in range(0,len(sort_confidence)):
        # print("Rule #{0}:".format(index+1))
    premise,conclusion = sort_confidence[index][0]



    # get_product_name('T382-6')
for index in range(0,len(sort_confidence)):
        # print("index: ", index)
        # print("Rule #{0}:".format(index+1))
    premise,conclusion = sort_confidence[index][0]
    premise_name = ", ".join(str(idx) for idx in premise)
    conclusion_name = str(conclusion)
    #     print("Rule: If a person recommends {0} they will also recommend {1}".format(premise_name,conclusion_name))
    #     print("- Confidence: {0:.1f}%".format(sort_confidence[index][1]))
    # # evaluation using test data
test_data = c_data[~c_data['CustomerID'].isin(range(200))]
test_data.head()
test_favor_by_users = dict((k,frozenset(v.values)) for k,v in test_data.groupby('CustomerID')['ProductID'])
correct_counts = defaultdict(int)
incorrect_counts = defaultdict(int)
for user,reviews in test_favor_by_users.items():
    for candidate_rule in candidate_rules:
        premise,conclusion = candidate_rule
        if premise.issubset(reviews):
            if conclusion in reviews:
                correct_counts[candidate_rule] += 1
            else:
                incorrect_counts[candidate_rule] += 1
test_confidence = {candidate_rule: correct_counts[candidate_rule] / float(correct_counts[candidate_rule]+incorrect_counts[candidate_rule])
                       for candidate_rule in rule_confidence}
obj.truncTable(credentials.host,  credentials.database, credentials.user, credentials.password) 

df = pd.DataFrame(columns=["id", "if_bought", "then_also", "created_at", "updated_at"])
for i in range(len(test_confidence)):
    premise,conclusion = sort_confidence[i][0]
    premise_name = ", ".join(str(idx) for idx in premise)
    conclusion_name = str(conclusion)
    df.loc[len(df)] = [len(df)+1,premise_name,conclusion_name,pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S"),pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")]

print(len(df))
obj.insertToDB(credentials.host,  credentials.database, credentials.user, credentials.password ,df.sort_values('id') )

#To read the final data in xlsx

db_connection = sql.connect(credentials.host,  credentials.database, credentials.user, credentials.password)
db_cursor = db_connection.cursor()
sql_ = "select * from recommendation_engine_tmp"

db_cursor.execute(sql_)

'''table_rows = db_cursor.fetchall()
data = pd.DataFrame(table_rows, columns = df.columns.tolist())
print(data)
data.to_excel("Final_data.xlsx", index=False)'''
