# Prerequisites and Installation
We assume Earth Engine Python API is installed and EE authorised as desribed [here](https://developers.google.com/earth-engine/python_install). From v0.3.4 onwards geeadd will only run on Python 3. Also with the new changes to the Earth Engine API library, the tool was completely modified to work with earthengine-api v0.1.127 and higher. Authenticate your earth engine client by using the following in your command line or terminal setup.

<b>
```
earthengine authenticate
```
</b>
Quick installation **```pip install geeadd```** or **```pip install geeadd --user```**

To install using github:

<b>
```
git clone https://github.com/samapriya/gee_asset_manager_addon
cd gee_asset_manager_addon && pip install -r requirements.txt
python setup.py install
```
</b>

The advantage of having it installed is being able to execute geeadd as any command line tool. I recommend installation within virtual environment. To install run

<b>
```
python setup.py develop or python setup.py install

In a linux distribution
sudo python setup.py develop or sudo python setup.py install
```
</b>
