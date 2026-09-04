<?php
/**
 * Moteur de recherche overlay — Une IA par jour
 *
 * À ajouter dans functions.php du thème enfant Kenta Artistic Blog.
 * Charge PapaParse (CDN), le CSS et le JS du moteur de recherche.
 *
 * Les fichiers recherche-overlay.css et recherche-overlay.js
 * doivent être placés dans le dossier du thème enfant :
 *   wp-content/themes/kenta-child/
 */
add_action( 'wp_enqueue_scripts', function () {

    // PapaParse — parsing CSV côté client
    wp_enqueue_script(
        'papaparse',
        'https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js',
        [],
        '5.4.1',
        true // chargé en footer
    );

    // CSS de l'overlay
    wp_enqueue_style(
        'recherche-overlay',
        get_stylesheet_directory_uri() . '/recherche-overlay.css',
        [],
        '1.0.0'
    );

    // JS de l'overlay (dépend de PapaParse)
    wp_enqueue_script(
        'recherche-overlay',
        get_stylesheet_directory_uri() . '/recherche-overlay.js',
        [ 'papaparse' ],
        '1.1.0',
        true // chargé en footer
    );

    // Langue + CSV correspondant, lus par recherche-overlay.js (roConfig).
    // EN : base-en (uneIAparjour/base-en, mirroir anglais dérivé de la
    // traduction). FR (et repli si Polylang n'est pas actif) : base FR
    // historique, inchangée.
    $lang = function_exists( 'pll_current_language' ) ? pll_current_language() : 'fr';
    wp_localize_script( 'recherche-overlay', 'roConfig', [
        'lang'   => $lang,
        'csvUrl' => $lang === 'en'
            ? 'https://raw.githubusercontent.com/uneIAparjour/base-en/main/base-uneiaparjour-en.csv'
            : 'https://raw.githubusercontent.com/uneIAparjour/base/main/base-uneiaparjour.csv',
    ] );

}, 20 );
