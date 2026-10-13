<?php
$config = require __DIR__ . '/config.php';
require __DIR__ . '/api_client.php';

$client = new ToshApiClient($config['api_base'], $config['api_timeout']);

// We accept id as home::away and resolve via /top10 + /match endpoints.
$id = $_GET['id'] ?? '';
$home = $away = '';
if (str_contains($id, '::')) {
    [$home, $away] = explode('::', $id, 2);
}

// The Python API exposes /match/{external_id}. In the mock data the external_id
// is not exposed to the frontend, so we fetch the Top10 and locate a match by team names.
$signals = $client->get('/top10') ?? [];
$match = null;
foreach ($signals as $s) {
    if ($s['home_team'] === $home && $s['away_team'] === $away) {
        $match = $s;
        break;
    }
}

// Rebuild match detail from top10 (limited view) if not found
if (!$match) {
    http_response_code(404);
    echo "Match not found.";
    exit;
}

// Fetch full detail via /match/{external_id} — but since external_id isn't
// exposed in the frontend we also try to guess it from the mock dataset.
$full = $client->get('/match/' . rawurlencode($match['league'] . '_M' . '1'));
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($home) ?> vs <?= htmlspecialchars($away) ?> — <?= htmlspecialchars($config['app_name']) ?></title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
    <div class="brand">
        <a class="back" href="index.php">← Back</a>
        <h1><?= htmlspecialchars($home) ?> <span class="vs">vs</span> <?= htmlspecialchars($away) ?></h1>
        <p><?= htmlspecialchars($match['league_name']) ?> · <?= htmlspecialchars(substr($match['kickoff'], 0, 16)) ?></p>
    </div>
</header>

<main>
<section class="detail-summary">
    <div><span>Recommended market</span><strong><?= htmlspecialchars($match['market']) ?></strong></div>
    <div><span>Model probability</span><strong><?= round($match['probability'] * 100, 1) ?>%</strong></div>
    <div><span>Fair odds</span><strong><?= number_format($match['fair_odds'], 2) ?></strong></div>
    <div><span>Best odds</span><strong><?= number_format($match['best_odds'], 2) ?></strong></div>
    <div><span>Expected value</span><strong><?= $match['ev'] >= 0 ? '+' : '' ?><?= round($match['ev'] * 100, 1) ?>%</strong></div>
    <div><span>Confidence</span><strong><?= htmlspecialchars($match['confidence_label']) ?> (<?= (int)$match['confidence'] ?>)</strong></div>
</section>

<?php if ($full && isset($full['markets'])): ?>
<section class="market-table">
    <h2>Full Market Breakdown</h2>
    <table>
        <thead>
            <tr><th>Market</th><th>Probability</th><th>Fair odds</th></tr>
        </thead>
        <tbody>
        <?php
        // Sort markets: most likely first, but keep families grouped.
        $order = ['1X2','DC','DNB','OU','BTTS','AH','CS'];
        $grouped = [];
        foreach ($full['markets'] as $m => $p) {
            $fam = explode(':', $m)[0];
            $grouped[$fam][$m] = $p;
        }
        foreach ($order as $fam) {
            if (empty($grouped[$fam])) continue;
            foreach ($grouped[$fam] as $m => $p) {
                printf(
                    '<tr><td>%s</td><td>%.1f%%</td><td>%.2f</td></tr>',
                    htmlspecialchars($m),
                    $p * 100,
                    $p > 0 ? 1 / $p : 0
                );
            }
        }
        ?>
        </tbody>
    </table>
</section>
<?php endif; ?>
</main>
</body>
</html>