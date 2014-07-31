zdash
=====

Dashboard For Zabbix

![zdash](https://raw.githubusercontent.com/zubbilo/zdash/master/doc/Zabbix_2.2_zdash.png)

# ZabbixAPI Used

*Metadata-Version: 1.0\n
Name: zabbix-api
Version: 0.1
Summary: Zabbix API
Home-page: https://github.com/gescheit/scripts
Author: Aleksandr Balezin
Author-email: gescheit@list.ru
License: GNU LGPL 2.1*

# ENGLISH

Dashboard for Zabbix on Python + ZabbixAPI 0.1

For BIG display in Helpdesk room

Additional functional - acnowledge's default lifetime is 3600 sec after submitting. After 3600 sec default acknowledges ignored and problem going to display on dashboard. There is some custom words that affect on ACK lifetime in variable DELAY.

No need to login to Zabbix GUI to access Dashboard. But not for acnowledging problem.

Macroses host-level resolving. Macroses template-level NOT!

UTF-8 encoding used on ack_message, ack_author, trigger_comment, trigger_description.

Supported on Zabbix SRV 2.2+
(Zabbix SRV 2.0+ can be supported after some modifications in API requests)

# РУССКИЙ

Панель для Zabbix на Python + ZabbixAPI 0.1

Для Больших мониторов в комнате технической поддержки.

Дополнительная фишка - комментарии (acknowledge) по умолчанию живут 1 час после выставления. Через 1 час не смотря на наличие ACK проблема всё равно выводится на панель. Варианты времени жизни ACK: 1 час, 22 часа, 29 дней, 179 дней (настраиваемые).

Логин в Zabbix для просмотра текущих сработавших триггеров не требуется, но для выставления комментария (acknowledge) - требуется.

Макросы уровня узла резолвятся нормально. Уровня шаблона - не было необходимости, поэтому - нет.

Русский язык поддерживается.

Совместимость с Zabbix SRV 2.2
(Zabbix SRV 2.0 может поддерживатся после изменения некоторых запросов к API)
