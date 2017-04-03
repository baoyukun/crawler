#coding=utf-8

import urllib2
import cookielib
import re
import time

class Statistics:
 
    def __init__(self):
        self.url = 'http://202.107.204.54:8080/cnipr/logoff.do?method=logoff'
        self.loginUrl = 'http://202.107.204.54:8080/cnipr/login.do?method=login'
        self.queryUrl = 'http://202.107.204.54:8080/cnipr/search.do?method=overviewSearch&area=cn'
        
        self.headers =  {
            'Host': '202.107.204.54:8080',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0',
            'Connection': 'keep-alive'
        }
        
        # Verification information
        self.postData = 'isCorpLogin=&userName=guest&password=123456'
        
        # Query form describe the form you have to fill out
        # strWhere: combination of all edited entries
        # txtD: year
        # txtH: classification number
        # txtQ: province name
        self.queryForm = 'presearchword=null&strWhere=&strSortMethod=-RELEVANCE&strDefautCols=%E4%B8%BB%E6%9D%83%E9%A1%B9%2C+%E5%90%8D%E7%A7%B0%2C+%E6%91%98%E8%A6%81&strStat=&iHitPointType=115&bContinue=&trsLastWhere=null&channelid=&channelid=&searchChannel=&strdb=14&strdb=15&strdb=16&iOption=2&sortcolumn=RELEVANCE&R1=&txtA=&txtB=&txtC=&txtD=&txtE=&txtF=&txtG=&txtH=&txtI=&txtJ=&txtK=&txtL=&txtM=&txtN=&txtP=&txtQ=&txtComb='
        
        self.cookies = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))
        
        # First link to the website
        result = self.opener.open( urllib2.Request(url = self.url, data = None, headers = self.headers) )
        
        # Log in
        self.headers['Referer'] = 'http://202.107.204.54:8080/cnipr/logoff.do?method=logoff'
        result = self.opener.open( urllib2.Request(url = self.loginUrl, data = self.postData, headers = self.headers) )
        
    def initRead(self, fileName):
        f1 = open('orKeywords.txt', 'a')
        f2 = open(fileName, 'r')
        
        keyWords = result = f2.readline()[:-1]
        for line in f2:
            result = result + '+or+' + line[:-1]
            keyWords = keyWords + ' or ' + line[:-1]
        
        f1.write(keyWords+'\n\n')
        f1.close()
        f2.close()
        return result
    
    def getPage(self, year, place, name):
        # Now it's time to enter keywords and search patents
        self.headers['Referer'] = 'http://202.107.204.54:8080/cnipr/search.do?method=showSearchForm&area=cn&channelId='
        # Use regular expressions to fill out the form
        queryData = re.sub(re.compile('txtQ=[^&]*&'), 'txtQ='+ place +'&',self.queryForm)
        queryData = re.sub(re.compile('txtH=[^&]*&'), 'txtH='+ name +'&',queryData)
        queryData = re.sub(re.compile('txtD=[^&]*&'), 'txtD='+ year +'&',queryData)
        queryData = re.sub(re.compile('strWhere=[^&]*&'), 'strWhere=pd=('+year+')+and+sic=('+name+')+and+co=('+place+')'+'&',queryData)
        
        result = self.opener.open( urllib2.Request(url = self.queryUrl, data = queryData, headers = self.headers) )
        return re.findall('\d+', re.findall('本次.*\d+条',result.read())[0])[0]
        
    def getResult(self):
        f = open('orKeywords.txt', 'w')
        f.truncate()
        f.close()
        
        field = [self.initRead('data/industry.txt'), self.initRead('data/agriculture.txt'),
                 self.initRead('data/construction.txt'), self.initRead('data/transportation.txt')]
        fieldName = ['工业', '农林牧渔', '建筑业', '交通运输']
        
        f = open('data/province.txt', 'r') 
        province = [f.readline()[:-1]]
        for line in f:
            province.append(line[:-1])
        f.close()
        
        f = open('result_classification.txt', 'w')
        f.truncate() 
        for year in range(2007,2015):
            for place in province:
                for name in range(0,4):
                    try:
                        result = self.getPage(str(year), place, field[name])
                        print str(year)+'   '+place+'  '+fieldName[name]+'  '+result+'\n'
                        f.write(str(year)+' '*15+place+' '*15+fieldName[name]+' '*15+result+'\n')
                        time.sleep(0.3)
                    except Exception,e:
                        print str(year)+'   '+place+'  '+fieldName[name]+'  '+'LINK ERROR\n'
                        f.write(str(year)+' '*15+place+' '*15+fieldName[name]+' '*15+'LINK ERROR\n')
                        time.sleep(0.3)
                        continue
        f.close()