# BAXI POWER METER


This component provides integration with Baxi branded power meter
## How to install
You can use HACS to install this integration as custom repository

If you are not using HACS, you must copy `baxi_power-meter` into your `custom_components` folder

## Configuration
Configuration via integration is recommended. Add an instance of `Baxi Power meter` using the UI:
![](https://github.com/vipial1/BAXI_power-meter/blob/main/images/integration.png?raw=true)

And follow the steps:
![](https://github.com/vipial1/BAXI_power-meter/blob/main/images/configuration.png?raw=true)
Integration will create an entity for energy consumption and a Device (only if configured using UI)

### Support for periods (Optional config)
In some countries, energy price depends on the billing period. That is possible to be configured in this integration, in order to do that
you have to add the periods in the next screen:
![](https://github.com/vipial1/BAXI_power-meter/blob/main/images/periods.png?raw=true)

Periods must follow the expression:
```
<Start Time 1>-<End Time 1>;<Start Time 2>-<End Time 2>
```
As example, periods for Spain market would like that:
```
10-14;18-22
8-10;14-18;22-24
0-8;weekend
```


## Work in progress
- Super huge refactor (code is completely shitty now)
- Lots (seriously, lots) of bugs to be fixed.
- Multidevice not tested, probably not working
- Translation
