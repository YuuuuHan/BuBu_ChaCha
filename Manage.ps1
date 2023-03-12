$info = "Hello, I am a shortcut for manage django project!"
$options = [System.Management.Automation.Host.ChoiceDescription[]] @("&Runserver", "&Make migrations", "M&igrate", "&Create super user", "&Shell plus", "&Test", "T&est - Now", "&Dump data to db", "&Load data to db", "&Quit")
$defaultChoice = 0
$opt = $Host.UI.PromptForChoice($Title , $info , $options, $defaultChoice)
$prefix = 'python manage.py '

switch($opt)
{
  0 { Invoke-Expression ($prefix + "runserver") }
  1 { Invoke-Expression ($prefix + "makemigrations") }
  2 { Invoke-Expression ($prefix + "migrate") }
  3 { Invoke-Expression ($prefix + "createsuperuser") }
  4 { Invoke-Expression ($prefix + "shell_plus") }
  5 { Invoke-Expression ($prefix + "test") }
  6 { Invoke-Expression ($prefix + "test --tag=now") }
  7 { Invoke-Expression ($prefix + "dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 4 > db_data.json") }
  8 { Invoke-Expression ($prefix + "loaddata db_data.json") }
}
