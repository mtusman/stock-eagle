Stock Eagle
======================

Keep up to date with your stock portfolio by receiving daily emails summarising the latest news articles related to companies in your portfolio

Example Use
======================
```python
from eagle import main

# You can list as many tickers as you like but take into account the longer the list the more time it will take.
tickers = ['AAPL', 'GOOG', 'TSLA', 'FB', 'SNAP','MSFT']

# This is your email address
# So far this programme only supports gmail.

_from = "adam.smith@gmail.com"
# Person you want to send the reports to - usually it's yourself
to = _from

# Your password for your email account
password = "Password1"

main(tickers, _from, to, password)
```
Example Email
======================
<p align="center"><img src="https://raw.githubusercontent.com/mtusman/Stock-Eagle/master/media/Screenshot_1.png" width=60%></p>

<p align="center"><img src="https://raw.githubusercontent.com/mtusman/Stock-Eagle/master/media/Screenshot_2.png" width=60%></p>

TODO
======================
-Add hotmail and yahoo mail support
<br>
-Allow users to add properties to personalize their stats report such as adding a 200 Moving Average etc..
<br>
-Improve the summarization algorithm to make it more efficient