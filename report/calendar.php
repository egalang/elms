<!DOCTYPE html>
<html>
    <head>
        <title>PHP Calendar</title>
    </head>
    <body>
        <?php
        $list = array(1=>"PMI: 12,345.00",9=>"FLTC: 123,456.00",15=>"IMC: 2,345.00",21=>"PLC: 34,123.00");
        $nmonth = idate("m");
        $month = date("F",strtotime("2023-".$nmonth."-01"))."<br>";
        echo "<h1>Monthly Outstanding and Funded Loans Report - $month</h1>";
        $days = cal_days_in_month(CAL_GREGORIAN,$nmonth,idate("y"))."<br>";
        $ndate = date("Y")."-".$nmonth."-1";
        $timestamp = strtotime($ndate);
        $day = date('D', $timestamp);
        $dayofweek = date('w', $timestamp);
        ?>
        <table border="1" width="100%">
            <thead><tr><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr></thead>
            <tbody>
                <?php
                    $w = intval($dayofweek);
                    $z = 1;
                    for ($y = 0; $y <= 5; $y++) {
                        echo "<tr>";
                        for ($x = 0; $x <= 6; $x++) {
                            if ($w<=0){
                                echo "<td><div style='height: 100px; width: 200px;'>$z<br>";
                                foreach ($list as $i => $val ) {
                                    if ( $i == $z ) {
                                        echo $val;
                                    }
                                }
                                $z++;
                                if ($z > intval($days)){
                                    $w = 12;
                                }
                            } else {
                                echo "<td>&nbsp;</td>";
                            }
                            $w = $w - 1;
                        }
                        echo "</tr>";
                    }
                ?>
            </tbody>
        </table>
    </body>
</html>
