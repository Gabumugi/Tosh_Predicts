<?php
$config = require __DIR__ . '/config.php';
require __DIR__ . '/api_client.php';

$client = new ToshApiClient($config['api_base'], $config['api_timeout']);

// Handle "refresh" action
if (($_GET['action'] ?? '') === 'refresh') {
    $client->post('/refresh');
    header('Location: index.php');
    exit;
}

$signals = $client->get('/top10') ?? [];
$health  = $client->get('/health') ?? ['built_at' => null];

$marketLabels = [
    '1X2'  => 'Match Result',
    'DC'   => 'Double Chance',
    'DNB'  => 'Draw No Bet',
    'OU'   => 'Over/Under',
    'BTTS' => 'Both Teams To Score',
    'AH'   => 'Asian Handicap',
    'CS'   => 'Correct Score',
];

function pretty_market(string $m): string {
    if (!str_contains($m, ':')) return $m;
    [$fam, $sel] = explode(':', $m, 2);
    $map = [
        '1X2'  => '1X2',
        'DC'   => 'Double Chance',
        'DNB'  => 'Draw No Bet',
        'OU'   => 'Over/Under',
        'BTTS' => 'BTTS',
        'AH'   => 'Asian Handicap',
        'CS'   => 'Correct Score',
    ];
    $label = $map[$fam] ?? $fam;
    return $label . ' · ' . str_replace(':', ' ', $sel);
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($config['app_name']) ?></title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
    <div class="brand">
        <span class="logo">TP</span>
        <div>
            <h1><?= htmlspecialchars($config['app_name']) ?></h1>
            <p><?= htmlspecialchars($config['app_tagline']) ?></p>
        </div>
    </div>
    <div class="actions">
        <span class="built-at">
            <?php if (!empty($health['built_at'])): ?>
                Updated: <?= htmlspecialchars(substr($health['built_at'], 0, 19)) ?> UTC
            <?php else: ?>
                Engine offline
            <?php endif; ?>
        </span>
        <a class="btn" href="?action=refresh">Rebuild signals</a>
    </div>
</header>

<main>
<?php if (empty($signals)): ?>
    <div class="empty">
        <h2>No signals yet</h2>
        <p>The prediction engine hasn't produced qualifying value bets.
           Click <strong>Rebuild signals</strong> to run the pipeline.</p>
    </div>
<?php else: ?>
    <section class="grid">
    <?php foreach ($signals as $s): ?>
        <?php
            $evPct = round($s['ev'] * 100, 1);
            $probPct = round($s['probability'] * 100, 1);
            $confClass = strtolower($s['confidence_label']);
        ?>
        <article class="card <?= $confClass ?>">
            <div class="rank">#<?= (int)$s['rank'] ?></div>
            <div class="head">
                <span class="league"><?= htmlspecialchars($s['league_name'] ?: $s['league']) ?></span>
                <span class="kickoff"><?= htmlspecialchars(substr($s['kickoff'], 0, 16)) ?></span>
            </div>
            <h2 class="teams">
                <?= htmlspecialchars($s['home_team']) ?>
                <span class="vs">vs</span>
                <?= htmlspecialchars($s['away_team']) ?>
            </h2>
            <div class="market"><?= htmlspecialchars(pretty_market($s['market'])) ?></div>
            <div class="stats">
                <div><span>Model P</span><strong><?= $probPct ?>%</strong></div>
                <div><span>Best odds</span><strong><?= number_format((float)$s['best_odds'], 2) ?></strong></div>
                <div><span>Fair odds</span><strong><?= number_format((float)$s['fair_odds'], 2) ?></strong></div>
                <div class="<?= $evPct >= 0 ? 'pos' : 'neg' ?>"><span>EV</span><strong><?= $evPct >= 0 ? '+' : '' ?><?= $evPct ?>%</strong></div>
            </div>
            <div class="footer">
                <span class="badge <?= $confClass ?>"><?= htmlspecialchars($s['confidence_label']) ?> · <?= (int)$s['confidence'] ?></span>
                <a class="detail-link" href="match.php?id=<?= urlencode($s['home_team']) ?>::<?= urlencode($s['away_team']) ?>">Details →</a>
            </div>
        </article>
    <?php endforeach; ?>
    </section>
<?php endif; ?>
</main>

<footer>
    <p>Tosh_Predicts — probabilities are model estimates, not guarantees. Bet responsibly.</p>
</footer>
</body>
</html>