from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureDescriptor:
    transformed_name: str
    source_feature: str
    category: str | None
    display_name: str


def remove_transformer_prefix(feature_name: str) -> str:
    """
    Remove sklearn ColumnTransformer prefixes.

    Example:
        numeric__TransactionAmt
        becomes
        TransactionAmt
    """
    if "__" not in feature_name:
        return feature_name

    return feature_name.split("__", maxsplit=1)[1]


def create_display_name(
    source_feature: str,
    category: str | None = None,
) -> str:
    readable_feature = source_feature.replace("_", " ").strip()

    if category:
        readable_category = category.replace("_", " ").strip()
        return f"{readable_feature}: {readable_category}"

    return readable_feature


def map_transformed_feature(
    transformed_name: str,
    raw_feature_names: list[str],
) -> FeatureDescriptor:
    """
    Map an encoded or transformed model feature back to its raw source.

    One-hot encoded feature examples:

        categorical__ProductCD_W
        categorical__card4_visa
        categorical__DeviceType_mobile
    """
    stripped_name = remove_transformer_prefix(transformed_name)

    source_feature = stripped_name
    category: str | None = None

    # Longest names are checked first to handle fields such as:
    # TransactionAmt_log and TransactionAmt.
    sorted_raw_names = sorted(
        raw_feature_names,
        key=len,
        reverse=True,
    )

    for raw_name in sorted_raw_names:
        if stripped_name == raw_name:
            source_feature = raw_name
            break

        encoded_prefix = f"{raw_name}_"

        if stripped_name.startswith(encoded_prefix):
            source_feature = raw_name
            category = stripped_name[len(encoded_prefix):]
            break

    return FeatureDescriptor(
        transformed_name=transformed_name,
        source_feature=source_feature,
        category=category,
        display_name=create_display_name(
            source_feature=source_feature,
            category=category,
        ),
    )


def map_transformed_features(
    transformed_names: list[str],
    raw_feature_names: list[str],
) -> list[FeatureDescriptor]:
    return [
        map_transformed_feature(
            transformed_name=name,
            raw_feature_names=raw_feature_names,
        )
        for name in transformed_names
    ]
