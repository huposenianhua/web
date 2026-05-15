<?php
namespace Detection;

class MobileDetect
{
    public function setUserAgent(string $userAgent): void {}
    public function isMobile(): bool { return false; }
    public function isTablet(): bool { return false; }
}