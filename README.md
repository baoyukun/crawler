# crawler_exercise
An exercice of crawler for getting patent data.

## 关于数据采集程序的说明  

程序需要在“中外专利信息服务平台”上不断提交表单，并抓取反馈结果，解析专利条数。主要思路为：
- 第一步 登录并存储cookie
- 第二步 模拟手工填写表单并提交
- 第三步 抓取反馈结果并解析答案
  
程序中添加了必要的注释，便于使用者后期扩展。
  
这里，"*crawler_mainClassification.py*"用于将行业搜索关键词填在“**主分类号**”表框中，而"*crawler_classification.py*"用于将行业搜索关键词填在“**分类号**”表框中。实验发现，如果将同一行业搜索关键词同时填入主分类号和分类号，则反馈结果与单独填入主分类号时的一致。另一发现是，填入主分类号得到的反馈结果总是小于填入分类号得到的反馈结果。  

两个程序的思想结构完全一致，只是表单部分略有不同，因此使用方法完全相同，这里以"*crawler_classification.py*"为例。首先，运行任何python程序最简单的方法当然是在程序所在路径的命令行中输入：
```python
   python programName.py
```
然而，因为这两个文件事实上只包含*Statistics*类，所以需要首先创建对象，而不是直接运行程序。
```python
   import crawler_classification
   crawler = crawler_classification.Statistics()
```
继而，该类提供了两个方法，一是*getPage()*，二是*getResult()*。  
前者允许对单个表项进行直接检索，即返回特定（公开公告日、国省代码、分类号）组合的绿色专利个数。
```python
   print crawler.getPage('2013','江苏','A01G23/00+or+A01G25/00+or+A01N25/00+or+A01N27/00+or+A01N29/00+or+A01N31/00')
```
上面的命令将给出江苏省2013年以上各类大项的绿色专利总和。  
**注意\:**
- 各项之间用*“+or+”*连接作为参数传递给程序
- 各大行业的or组合已由程序生成，见程序文件夹中的*orKeywords.txt*文件，可直接复制用于在网站上进行手动验证
  
当然，你也可以只考察一个项目领域，比如
```python
   print crawler.getPage('2013','江苏','A01G23/00')
```
第二种方法getResult()则允许直接给出最终结果，即2007-2014年之间各省在各大行业的绿色专利数列表。
```python
   crawler.getResult()
```
最终的结果保存在名为*result*的文本文件中，可直接导入excel文件，进行后续分析。
