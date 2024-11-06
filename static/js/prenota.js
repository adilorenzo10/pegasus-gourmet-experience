// Inizializza l'evento sul cambiamento della data
$("#data").on("change", function() {
    $(".sez-orari, .riga-pulsante-prenota, .errore-nessun-orario").addClass("d-none");
    var dataSelezionata = $(this).val();
    verificaPrenotazione(dataSelezionata);
});

// Verifica se l'utente ha già una prenotazione per la data selezionata
function verificaPrenotazione(dataSelezionata) {
    $.ajax({
        url: "/ajax/verifica_data_prenotazione",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ "data": dataSelezionata }),
        success: function(response) {
            if (response.prenotazione_esiste) {
                // Se esiste già una prenotazione, mostra il messaggio specifico
                $(".errore-nessun-orario .alert").text("Non sono disponibili orari perché hai già prenotato un tavolo nella data selezionata. È possibile prenotare un solo tavolo al giorno.");
                $(".errore-nessun-orario").removeClass("d-none");
            } else {
                // Se non ci sono prenotazioni, carica gli orari disponibili
                caricaOrariDisponibili(dataSelezionata);
            }
        },
        error: function(error) {
            console.log("Errore durante la verifica della prenotazione per la data selezionata.");
            console.log(error);
        }
    });
}

// Carica gli orari disponibili per la data selezionata
function caricaOrariDisponibili(dataSelezionata) {
    $.ajax({
        url: "/ajax/orari_disponibili",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ "data": dataSelezionata }),
        success: function(response) {
            console.log(response);
            mostraOrariDisponibili(response, dataSelezionata);
        },
        error: function(error) {
            console.log("Errore durante il recupero degli orari disponibili.");
            console.log(error);
        }
    });
}

// Mostra gli orari disponibili nel DOM
function mostraOrariDisponibili(orariDisponibili, dataSelezionata) {
    $(".input-orario, .label-orario").hide();
    var oggi = new Date().toISOString().split("T")[0]; // Ottiene la data di oggi in formato YYYY-MM-DD
    var oraCorrente = new Date(); // Ora corrente con ore e minuti
    var orariDisponibiliCount = 0;

    if (orariDisponibili.length > 0) {
        orariDisponibili.forEach(function(orario) {
            if (dataSelezionata === oggi) {
                var orarioData = new Date();
                var [ore, minuti] = orario.orario.split(":").map(Number);
                orarioData.setHours(ore, minuti, 0);

                if (orarioData.getTime() - oraCorrente.getTime() >= 60 * 60 * 1000) {
                    mostraOrario(orario.id);
                    orariDisponibiliCount++;
                }
            } else {
                mostraOrario(orario.id);
                orariDisponibiliCount++;
            }
        });

        if (orariDisponibiliCount > 0) {
            $(".sez-orari, .riga-pulsante-prenota").removeClass("d-none");
        } else {
            $(".errore-nessun-orario .alert").text("Nessun orario disponibile nella data selezionata. Scegli un altro giorno!");
            $(".errore-nessun-orario").removeClass("d-none");
        }
    } else {
        $(".errore-nessun-orario .alert").text("Nessun orario disponibile nella data selezionata. Scegli un altro giorno!");
        $(".errore-nessun-orario").removeClass("d-none");
    }
}

// Funzione di supporto per mostrare l'orario nel DOM
function mostraOrario(orarioId) {
    $(`#orario-${orarioId}`).show();
    $(`label[for="orario-${orarioId}"]`).show();
}
