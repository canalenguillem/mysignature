// =====================================================================
// Plataforma de Firma Digital eIDAS — Inicialización MongoDB
// Referencia: docs/DATABASE.md §2
// Ejecutado por el contenedor mongo en el primer arranque
// (docker-entrypoint-initdb.d). Se ejecuta sobre MONGO_INITDB_DATABASE.
// =====================================================================

// La colección `documents` guarda los binarios de los PDFs (original/firmado).
db.createCollection("documents", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "document_id", "original_pdf", "created_at"],
      properties: {
        _id: { bsonType: "objectId" },
        document_id: { bsonType: "string" },   // FK a documents.id en MariaDB
        original_pdf: { bsonType: "binData" },  // PDF original en binario
        signed_pdf: { bsonType: "binData" },    // PDF firmado (si existe)
        file_metadata: {
          bsonType: "object",
          properties: {
            filename: { bsonType: "string" },
            size: { bsonType: "int" },
            mime_type: { bsonType: "string" },
            pages: { bsonType: "int" }
          }
        },
        versions: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              version_number: { bsonType: "int" },
              pdf_data: { bsonType: "binData" },
              created_at: { bsonType: "date" },
              created_by_id: { bsonType: "long" }
            }
          }
        },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

db.documents.createIndex({ document_id: 1 }, { unique: true });
db.documents.createIndex({ created_at: -1 });

// La colección `signature_metadata` guarda firma binaria + token TSA.
db.createCollection("signature_metadata", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "signature_id", "document_id"],
      properties: {
        _id: { bsonType: "objectId" },
        signature_id: { bsonType: "long" },     // FK a signatures.id en MariaDB
        document_id: { bsonType: "string" },
        signer_cert_pem: { bsonType: "string" },
        signature_binary: { bsonType: "binData" },
        tsa_response_der: { bsonType: "binData" },
        timestamps: {
          bsonType: "object",
          properties: {
            signed_at: { bsonType: "date" },
            timestamp_from_tsa: { bsonType: "date" },
            audit_logged_at: { bsonType: "date" }
          }
        },
        algorithms: {
          bsonType: "object",
          properties: {
            signature_algorithm: { bsonType: "string" },
            hash_algorithm: { bsonType: "string" }
          }
        }
      }
    }
  }
});

db.signature_metadata.createIndex({ signature_id: 1 }, { unique: true });
db.signature_metadata.createIndex({ document_id: 1 });
db.signature_metadata.createIndex({ "timestamps.signed_at": -1 });

print("MongoDB inicializado: colecciones documents y signature_metadata creadas.");
