#!/usr/bin/env sh
# AngaeBot Bridge 0.1: use official Gradle Wrapper JAR.
APP_HOME=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
JAR="$APP_HOME/gradle/wrapper/gradle-wrapper.jar"
if [ ! -f "$JAR" ]; then
  echo 'Official Gradle wrapper JAR missing. Download the verified Gradle 8.14.3 wrapper JAR to gradle/wrapper/gradle-wrapper.jar.' >&2
  exit 1
fi
if [ -n "$JAVA_HOME" ]; then JAVA="$JAVA_HOME/bin/java"; else JAVA=java; fi
exec "$JAVA" -Xmx64m -Xms64m -cp "$JAR" org.gradle.wrapper.GradleWrapperMain "$@"
