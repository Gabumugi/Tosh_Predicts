<?php
/**
 * Tiny curl wrapper around the Python API.
 */
class ToshApiClient
{
    private string $base;
    private int $timeout;

    public function __construct(string $base, int $timeout = 8)
    {
        $this->base = rtrim($base, '/');
        $this->timeout = $timeout;
    }

    public function get(string $path, array $query = []): ?array
    {
        $url = $this->base . $path;
        if ($query) {
            $url .= '?' . http_build_query($query);
        }
        return $this->request('GET', $url);
    }

    public function post(string $path, array $body = []): ?array
    {
        return $this->request('POST', $this->base . $path, $body);
    }

    private function request(string $method, string $url, ?array $body = null): ?array
    {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => $this->timeout,
            CURLOPT_CUSTOMREQUEST  => $method,
            CURLOPT_HTTPHEADER     => ['Accept: application/json', 'Content-Type: application/json'],
        ]);
        if ($body !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
        }
        $raw = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err  = curl_error($ch);
        curl_close($ch);

        if ($raw === false || $code >= 400) {
            error_log("[ToshApiClient] $method $url -> $code $err");
            return null;
        }
        $decoded = json_decode($raw, true);
        return is_array($decoded) ? $decoded : null;
    }
}