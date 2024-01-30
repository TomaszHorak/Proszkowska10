# Proszkowska10
I decided to automate my garden watering system. Instead of choosing out of the box market solutions I started to build custom electronic system.
Hardware:
- Raspberry PI
- DC relays
- power source
Backend software:
- OS: standard Debian installed in Raspberry
- Application: simple scripts written in Python controling GPIO ports of Raspberry steering water valves
Frontend software:
- Android custom application representing status of each water valve and allowing create matrixes to control watering time for every watering section of my garden
- no web UI so far

As solution was stabilised I've extended it with following features:
- dedicated API allowing to control particular areas of automation (lights, heating, audio etc)
- control of choosen house lights
- audio system: another Raspberry PI device with KODI and connected audio amplifiers
- sauna control: for my custom sauna house I can control switch on-off time, temperature and lights. Here dedicated NodeMCU device installed in sauna using my Proszwska10 API
- house heating: every room heater has its own dedicated valve which is controlled via relays connected to Raspberry. Again the same matrix used for waterng can control temperature in every room depending on time and date. Every room is equipped with temprature sensor based on NodeMCU

Future:
- build Web UI
- new are: surviliance, cameras around the house

To deploy my project in your location you have to:
- install hardware, I used Raspberry but you can choose different platform
- configure  
