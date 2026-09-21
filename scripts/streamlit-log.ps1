# Preserve UTF-8 from Python's pipe through both the console and the log file.
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$writer = [IO.StreamWriter]::new($env:LOGFILE, $true, [Text.UTF8Encoding]::new($false))
$writer.AutoFlush = $true
try {
    while ($null -ne ($line = [Console]::ReadLine())) {
        [Console]::WriteLine($line)
        $writer.WriteLine($line)
    }
} finally {
    $writer.Dispose()
}
