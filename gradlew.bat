@echo off
setlocal
rem AngaeBot Bridge 0.1 Gradle wrapper; official JAR provisioned by scripts\prepare-wrapper.ps1
set "PROJECT_DIR=%~dp0"
set "WRAPPER_JAR=%PROJECT_DIR%gradle\wrapper\gradle-wrapper.jar"
if not exist "%WRAPPER_JAR%" (
  echo [ERROR] Official Gradle wrapper JAR is missing.
  echo Run: powershell -ExecutionPolicy Bypass -File scripts\prepare-wrapper.ps1
  exit /b 1
)
if defined JAVA_HOME (
  set "JAVA_EXE=%JAVA_HOME%\bin\java.exe"
) else (
  set "JAVA_EXE=java.exe"
)
"%JAVA_EXE%" -Xmx64m -Xms64m -cp "%WRAPPER_JAR%" org.gradle.wrapper.GradleWrapperMain %*
exit /b %ERRORLEVEL%
