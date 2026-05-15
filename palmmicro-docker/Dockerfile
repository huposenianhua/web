FROM php:8.2-apache

ENV TZ=Asia/Shanghai

RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    libzip-dev \
    libonig-dev \
    unzip \
    curl \
    cron \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
    mysqli \
    gd \
    mbstring \
    zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN a2enmod rewrite

COPY apache/000-default.conf /etc/apache2/sites-available/000-default.conf

COPY cron/palmmicro-cron /etc/cron.d/palmmicro-cron
COPY cron/fetch_morning.sh /usr/local/bin/fetch_morning.sh
COPY cron/fetch_afternoon.sh /usr/local/bin/fetch_afternoon.sh
COPY cron/fetch_evening.sh /usr/local/bin/fetch_evening.sh
RUN chmod 0644 /etc/cron.d/palmmicro-cron && \
    chmod +x /usr/local/bin/fetch_morning.sh /usr/local/bin/fetch_afternoon.sh /usr/local/bin/fetch_evening.sh && \
    crontab /etc/cron.d/palmmicro-cron && \
    touch /var/log/cron.log

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN mkdir -p /var/www/html/woody/res/debug && \
    chown -R www-data:www-data /var/www/html

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["apache2-foreground"]
