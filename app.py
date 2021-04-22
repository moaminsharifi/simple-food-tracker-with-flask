from datetime import datetime
from flask import Flask, jsonify, request, redirect, session, render_template, g 
from database import connect_db, get_db
from collections import defaultdict

# app config
app = Flask(__name__)
app.config.update(
    TESTING=True,
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/')

######## APP ERROR HANDLER ########

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

######## Funcitions ########


def make_pretty_date(date: int) -> str:
    """Make a pertty date
    
    >>> make_pretty_date(20210423)
    April 23 , 2021
    >>> make_pretty_date(20210408)
    April 08 , 2021


    Parameters
    ----------
    date : int
        date as integer like 20210423

    Returns
    -------
    str
        string Like April 23 , 2021
    """
    date_string = str(date)
    assert len(date_string) >= 8 , 'date must be at least 8 characters'

    dt = datetime.strptime(str(date_string), '%Y%m%d')
    
    return datetime.strftime(dt, '%B  %d  , %Y')


def process_date_results(data :dict, date_key:str ='entry_date') -> dict: 
    """Processes the date_date and perturbation date

    >>>process_date_results({'entry_date':20210423})
    {'entry_date':20210423 , 'pertty_date':'April 23 , 2021'}
    
    >>>process_date_results({'entry_date':20210408})
    {'entry_date':20210408 , 'pertty_date':'April 08 , 2021'}

    Parameters
    ----------
    data : dict
        data as sqlite3.Row type
    date_key : str, optional
        key where store data on it, by default 'entry_date'

    Returns
    -------
    dict
        result with 'entry_date' and 'pertty_date' key
    """
    
    assert date_key in data, f'{date_key} key not exist in {data.keys()}'
   

    return {
        {'entry_date': data['entry_date'],
         'pertty_date': make_pretty_date(data['entry_date'])}
    }


######## Routes ########

@app.route('/', methods=['Get', 'POST'])
def index():
    
    db = get_db()

    if request.method == 'POST':
        date = request.form['date']
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            database_date = datetime.strftime(dt, '%Y%m%d')
        except:
            # make error
            return 'err'

        db.execute('insert into log_date (entry_date) values (?)',
                   [database_date])
        db.commit()

  
    cur = db.execute('''select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories 
                        from log_date 
                        left join food_date on food_date.log_date_id = log_date.id 
                        left join food on food.id = food_date.food_id 
                        group by log_date.id order by log_date.entry_date desc''')
    results = [dict(row) for row in cur.fetchall()]
  
    
    for item in results:
        item['pretty_date'] = make_pretty_date(item['entry_date'])
        
    return render_template('home.html', results=results)


@app.route('/view/<date>', methods=['GET', 'POST'])  # date pattern 20210423
def view(date):

    

    db = get_db()
    cur = db.execute(
        'select id,entry_date from log_date where entry_date = ? ', [date])
    date_result = cur.fetchone()

    
    if request.method == 'POST':
        db.execute('insert into food_date (food_id, log_date_id) values (? , ?) ', [
                   request.form['food_id'], date_result['id']])
        db.commit()
        
    pretty_date = make_pretty_date(date_result['entry_date'])

    food_cur = db.execute('select id,name from food')
    food_results = food_cur.fetchall()


    log_cur = db.execute('select food.name, food.protein, food.carbohydrates, food.fat, food.calories from log_date join food_date on food_date.log_date_id = log_date.id join food on food.id = food_date.food_id where log_date.entry_date = ?', [date])
    log_results = log_cur.fetchall()


    totals = {
        'protein':0,
        'carbohydrates':0,
        'fat':0,
        'calories':0,
    }
    for food in log_results:
        for key in totals.keys():
            totals[key] += + food[key]

    return render_template('day.html',
                            pretty_date=pretty_date,
                            food_results=food_results,
                            date=date,
                            log_results=log_results,
                            totals=totals)

@app.route('/food', methods=['GET','POST'])
def food():
    db = get_db()

    if request.method == 'POST':
        name, protein, carbohydrates, fat = request.form[
            'food'], int(request.form['protein']), int(request.form['carbohydrates']), int(request.form['fat'])

        calories = protein * 4  + carbohydrates * 4 + fat * 9
        
        db.execute('insert into food (name, protein, carbohydrates , fat , calories) values (? , ?, ?, ?, ?)',\
            [name , protein, carbohydrates , fat , calories])
        db.commit()

        # return f"Name : {request.form['food']} , Protein: {request.form['protein']}  ,Carbs: {request.form['carbohydrates']},  Fat: {request.form['fat']}"
    cur = db.execute('select name, protein, carbohydrates , fat , calories from food')
    results = cur.fetchall()

    return render_template('add_food.html', results=results)
