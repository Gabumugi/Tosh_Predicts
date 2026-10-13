<?php
/**
 * Tosh_Predicts PHP frontend configuration.
 */
return [
    // Base URL of the Python FastAPI service
    'api_base'   => getenv('TOSH_API_BASE') ?: 'http://127.0.0.1:8000',
    'api_timeout'=> 8,
    'app_name'   => 'Tosh_Predicts',
    'app_tagline'=> 'Top 10 value bets across Europe & Brazil',
];